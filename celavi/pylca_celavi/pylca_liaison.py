import os
import sys
import time
import logging
from pathlib import Path
from typing import Any, List, Tuple

import pandas as pd
import numpy as np
from celavi.pylca_celavi.liaison.liaison_model import main_run

logger = logging.getLogger(__name__)


def liaison_lci(
    f_d: pd.DataFrame,
    yr: int,
    fac_id: int,
    stage: str,
    material: str,
    unit: str,
    route_id: str,
    state: str,
    liaison_process_bridge: str,
    additional_inventories: List[Any],
    liaison_reeds_project_name: str,
    liaison_reeds_database: str,
    celavi_lca_project: str,
    pv_module_chars: Any,
    data_dir: str,
    verbose: bool,
    bw: Any,
) -> Tuple[pd.DataFrame, float]:
    """
    Run a LiAISON LCI calculation for a single process and flow.

    Parameters
    ----------
    f_d
        Foreground flows DataFrame from DES, deduplicated and non-null.
    yr
        Original model year.
    fac_id
        Facility identifier.
    stage
        Supply chain stage (activity) key.
    material
        Material being processed.
    unit
        Unit of the material flow.
    route_id
        Transportation route UUID.
    state
        Geographic region code (e.g., state).
    liaison_process_bridge
        Path to CSV mapping stages to Ecoinvent processes.
    additional_inventories
        Extra inventory sources for LiAISON.
    liaison_reeds_project_name
        Base name of the ReEDS project in Brightway.
    liaison_reeds_database
        Base name of the ReEDS database.
    celavi_lca_project
        Base name of the Celavi LCA project.
    pv_module_chars
        Photovoltaic module characteristics dict.
    data_dir
        Directory for auxiliary data.
    verbose
        If True, prints extra progress.
    bw
        Imported Brightway2 module.

    Returns
    -------
    res_df
        DataFrame of LCI results, or empty if computation skipped/failed.
    quantity
        Functional unit processed.
    """
    logger.debug(
        "liaison_lci start: year=%d, stage=%s, material=%s, state=%s",
        yr, stage, material, state,
    )

    # Clean input
    f_d = f_d.drop_duplicates().dropna()
    start_time = time.time()

    # Adjust year to available LCI
    if yr < 2024:
        year_for_lci = 2024
    else:
        year_for_lci = yr if yr % 2 == 0 else yr - (yr % 2)
    logger.debug(
        "Adjusted year from %d to %d for LCI availability", yr, year_for_lci
    )

    # Sanity check
    if len(f_d) != 1:
        logger.warning(
            "Expected single-row input for LCA, got %d rows; skipping computation",
            len(f_d),
        )
        return pd.DataFrame(), 0.0

    f_d = f_d.reset_index(drop=True)
    flow_name = f_d.at[0, 'flow name']
    quantity = float(f_d.at[0, 'flow quantity'])

    # Load process bridge
    bridge_path = Path(liaison_process_bridge)
    bridge_df = pd.read_csv(bridge_path)
    proc_map = (
        bridge_df
        .loc[bridge_df['Activities'] == stage, ['Activities', 'Ecoinvent', 'Unit', 'Celavi Unit']]
        .dropna()
        .reset_index(drop=True)
    )

    if proc_map.empty:
        logger.error(
            "No matching process for stage '%s' in bridge file %s", stage, bridge_path
        )
        return pd.DataFrame(), quantity
    elif len(proc_map) > 1:
        logger.error(
            "Multiple entries for stage '%s' in bridge file %s: %d matches",
            stage, bridge_path, len(proc_map)
        )
        return pd.DataFrame(), quantity

    process_name = proc_map.at[0, 'Ecoinvent']
    expected_unit = proc_map.at[0, 'Unit']
    celavi_unit = proc_map.at[0, 'Celavi Unit']

    # Unit validation
    if unit != celavi_unit:
        logger.warning(
            "Unit mismatch: provided '%s', expected '%s' for stage %s",
            unit, celavi_unit, stage,
        )

    # Prepare Brightway project/database names
    proj_year = f"{liaison_reeds_project_name}{year_for_lci}"
    db_year = liaison_reeds_database
    lca_proj = f"{celavi_lca_project}{year_for_lci}"
    unique_tag = str(np.random.randint(1e8))
    new_proj = f"{lca_proj}_{unique_tag}"

    # Nested corrections
    def correct_natural_land_transformation():
        methods = [m for m in bw.methods if "natural land transformation" in m[1]]
        whitelist = set([
            "forest", "grassland, natural", "sea", "ocean", "inland waterbody",
            "lake, natural", "river, natural", "seabed, natural", "shrub land", "snow",
            "unspecified", "wetland", "bare area",
        ])
        for m in methods:
            df_cf = bw.Method(m).load()
            filtered = [cf for cf in df_cf if any(n in bw.get_activity(cf[0])["name"] for n in whitelist)]
            bw.Method(m).write(filtered)
        logger.debug("Corrected natural land transformation methods: %d methods updated", len(methods))

    def correct_bigcc_copper_use():
        acts = [
            "electricity production, at BIGCC power plant, no CCS",
            "electricity production, at BIGCC power plant, pre, pipeline 200km, storage 1000m",
            "electricity production, at BIGCC power plant, pre, pipeline 400km, storage 3000m",
        ]
        for ds in bw.Database(db_year):
            if ds['name'] in acts:
                for exc in ds.exchanges():
                    if exc['name'] == "Construction, BIGCC power plant 450MW":
                        exc['amount'] = 1.01e-11
                        exc.save()
        logger.debug("Corrected BIGCC copper use in database %s", db_year)

    # Copy and reset project
    try:
        bw.projects.delete_project(new_proj, delete_dir=True)
    except Exception:
        pass
    bw.projects.set_current(proj_year)
    bw.projects.copy_project(new_proj, switch=False)
    bw.projects.set_current(new_proj)
    correct_natural_land_transformation()
    correct_bigcc_copper_use()

    # Run LCA
    logger.info(
        "Running LCA: project=%s, process=%s, region=%s, quantity=%.3f",
        new_proj, process_name, state, quantity,
    )
    res_df = main_run(
        lca_project=lca_proj,
        updated_project_name=proj_year,
        year_of_study=year_for_lci,
        results_filename=f"{celavi_lca_project}{year_for_lci}{state}",
        mc_foreground_flag=False,
        lca_flag=True,
        region_sensitivity_flag=False,
        edit_ecoinvent_user_controlled=True,
        region=state,
        data_dir=data_dir,
        input_dir=None,
        primary_process=process_name,
        process_under_study=process_name,
        location_under_study=state,
        unit_under_study=expected_unit,
        updated_database=db_year,
        mc_runs=0,
        functional_unit=quantity,
        inventory_filename=additional_inventories,
        pv_module_chars=pv_module_chars,
        output_dir=None,
        bw=bw,
    )

    # Clean up project
    try:
        bw.projects.delete_project(bw.projects.current, delete_dir=True)
    except Exception:
        logging.error("Issue with deleting project directory %s",bw.projects.current)

    # Validate results
    if res_df.empty:
        logger.error(
            "LCA calculation returned empty results for %s, %s, %s", year_for_lci, stage, material
        )
        sys.exit(1)

    # Annotate results
    res_df = res_df.assign(
        year=yr,
        facility_id=fac_id,
        stage=stage,
        material=material,
        route_id=route_id,
        state=state,
    )

    elapsed = time.time() - start_time
    logger.info(
        "Completed LCA for %s @ %s in %.1f seconds", stage, state, elapsed
    )

    return res_df, quantity
