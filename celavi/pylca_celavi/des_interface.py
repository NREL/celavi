import os
from pathlib import Path
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from celavi.pylca_celavi.pylca_liaison import liaison_lci

logger = logging.getLogger(__name__)


class PylcaCelavi:
    """
    Interface for performing precomputed or live LCA calculations via LiAISON.

    Attributes
    ----------
    lcia_des_path : Path
        Path to the output CSV that receives calculated impacts.
    shortcutlca_path : Path
        Path to the cache of previously computed impacts.
    data_sent_path : Path
        Path to record input data sent for LCA processing.
    brightway_dir : Path
        Directory for Brightway2 database configuration.
    liaison_reeds_project_name : str
    liaison_reeds_database : str
    celavi_lca_project : str
    liaison_process_bridge : Any
    additional_inventories : List[Any]
    pv_module_chars : Dict[str, Any]
    use_shortcut_lca_calculations : bool
    verbose : bool
    run_id : int
    data_dir : Path
    bw : module
        Imported Brightway2 module, available after initialization.
    """

    def __init__(
        self,
        data_dir: str,
        liaison_params: Dict[str, str],
        lcia_des_filename: str,
        shortcutlca_filename: str,
        brightway_dir: str,
        liaison_process_bridge: Any,
        additional_inventories: List[Any],
        data_sent_to_liaison: str,
        pv_module_chars: Dict[str, Any],
        use_shortcut_lca_calculations: bool = False,
        verbose: bool = False,
        run: int = 0,
    ) -> None:
        """
        Initialize LCA runner, configure Brightway, and clear previous results.

        Parameters
        ----------
        data_dir
            Directory for intermediate data files.
        liaison_params
            Keys: 'liaison_reeds_project_name', 'liaison_reeds_database', 'celavi_lca_project'.
        lcia_des_filename
            CSV file path to append final LCIA results.
        shortcutlca_filename
            CSV file path to cache shortcut results.
        brightway_dir
            Directory for Brightway2 configuration.
        liaison_process_bridge
            Bridge object for LiAISON process definitions.
        additional_inventories
            Inventories to include in LiAISON.
        data_sent_to_liaison
            CSV file path to record input flows sent to LiAISON.
        pv_module_chars
            PV module characteristics for the LiAISON model.
        use_shortcut_lca_calculations
            If True, attempt to read impacts from the cache.
        verbose
            Enable debug-level logging.
        run
            Identifier for the model run.
        """
        # Convert paths
        self.data_dir = Path(data_dir)
        self.lcia_des_path = Path(lcia_des_filename)
        self.shortcutlca_path = Path(shortcutlca_filename)
        self.data_sent_path = Path(data_sent_to_liaison)
        self.brightway_dir = Path(brightway_dir)

        # Liaison parameters
        self.liaison_reeds_project_name = liaison_params["liaison_reeds_project_name"]
        self.liaison_reeds_database = liaison_params["liaison_reeds_database"]
        self.celavi_lca_project = liaison_params["celavi_lca_project"]

        # Other configuration
        self.liaison_process_bridge = liaison_process_bridge
        self.additional_inventories = additional_inventories
        self.pv_module_chars = pv_module_chars
        self.use_shortcut_lca_calculations = use_shortcut_lca_calculations
        self.verbose = verbose
        self.run_id = run

        #ShortcutLCA file creator
        self.lca_database = pd.read_csv(
                self.shortcutlca_path,
                header=None,
        )
        self.lca_database.columns = ['lcia','unit','year','method','stage','state','value']


        
        # Set up Brightway environment variable
        os.environ["BRIGHTWAY2_DIR"] = str(self.brightway_dir)
        if self.verbose:
            print("Importing Brightway2 module...", flush=True)
        import brightway2 as bw
        self.bw = bw
        if self.verbose:
            print("Imported Brightway2", flush=True)

        logger.info("Configuring Brightway at %s", self.brightway_dir)

        # Clean previous results if present
        try:
            self.lcia_des_path.unlink()
            logger.debug("Deleted old LCIA output: %s", self.lcia_des_path)
        except FileNotFoundError:
            logger.debug("No existing LCIA output to delete: %s", self.lcia_des_path)

    def lca_performance_improvement(
        self,
        df: pd.DataFrame,
        state: str,
        stage: str,
        year: int,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Read cached LCIA impacts to skip live calculation where possible.

        Parameters
        ----------
        df
            Input flows DataFrame for a specific region and process stage.
        state
            State identifier (e.g., 'US-CA').
        stage
            Supply chain stage.
        year
            Model year.

        Returns
        -------
        missing_df
            Rows needing live LCA calculation.
        result_df
            Cached impacts for matching rows.
        """

        try:
            # Read cache without header, assign expected columns
            cache_df = pd.read_csv(
                self.shortcutlca_path,
                header=None,
            )
            cache_df = cache_df.dropna(axis=1, how='all')
            #cache_df.columns = ['lcia','cached_value','unit','year','method','stage','state']
            cache_df.columns = ['lcia','unit','year','method','stage','state','cached_value']
            # Ensure consistent types for merge keys
            for col in ['stage', 'year', 'state']:
                df[col] = df[col].astype(str)
                cache_df[col] = cache_df[col].astype(str)

            merged = df.merge(
                cache_df,
                on=['stage', 'year', 'state'],
                how='outer',
                indicator=True,
            )

            missing_df = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])
            result_df = merged[merged['_merge'] == 'both'].drop(columns=['_merge'])
            if result_df.empty:
                logger.warning(
                    "Shortcut LCA cache missing entry for %s, %s, %d",
                    state, stage, year,
                )
            else:
                logger.warning(
                    "Using shortcut LCA cache for %s, %s, %d: %d entries",
                    state, stage, year, len(result_df)
                )

            # Apply cached factor
            result_df['value'] = (
                result_df['flow quantity'] * result_df['cached_value']
            )
            cols = [
                'lcia', 'unit', 'year', 'method',
                'facility_id', 'stage', 'material', 'route_id', 'state','value'
            ]
            return missing_df, result_df[cols]

        except:
            logger.warning(
                "Shortcut LCA cache not read or column reading issues at %s", self.shortcutlca_path
            )
            return df, pd.DataFrame()

    def pylca_run_main(
        self, df: pd.DataFrame, verbose: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Execute LiAISON LCA runs, using cache where enabled.

        Parameters
        ----------
        df
            DataFrame of flows with columns including 'flow quantity', 'state', etc.
        verbose
            Override instance verbosity for this call.

        Returns
        -------
        pd.DataFrame
            Combined LCIA results with columns:
            ['year', 'facility_id', 'material', 'route_id', 'stage', 'state',
             'impacts', 'impact', 'unit', 'run', 'comment']
        """
        if verbose is None:
            verbose = self.verbose

        # Filter zero flows
        df = df.loc[df["flow quantity"] != 0].reset_index(drop=True)
        if df.empty:
            logger.info("No nonzero flows to process.")
            return pd.DataFrame()

        # Record inputs
        df.to_csv(self.data_sent_path, mode="a", header=False, index=False)

        results: List[pd.DataFrame] = []
        states = df["state"].unique()

        for raw_state in states:
            region = f"US-{raw_state}" if len(raw_state) == 2 else raw_state
            subset = df[df["state"] == raw_state].copy()
            subset["state"] = region

            for idx, row in subset.iterrows():
                year = int(row["year"])
                stage = row["stage"]
                material = row["material"]
                facility_id = row["facility_id"]
                route_id = str(row["route_id"])
                unit = row["flow unit"]

                original_year = year
                if year < 2024:
                    year = 2024
                    subset.at[idx, "year"] = year

                if self.use_shortcut_lca_calculations:
                    to_calc, cached = self.lca_performance_improvement(
                        subset.loc[[idx]], region, stage, original_year
                    )
                    to_calc["route_id"] = route_id
                else:
                    to_calc = subset.loc[[idx]]
                    cached = pd.DataFrame()

                live = pd.DataFrame()
                if not to_calc.empty and to_calc["flow quantity"].sum() != 0:
                    flow_df = to_calc.assign(**{"flow name": to_calc["material"] + ", " + stage})[
                        ["flow name", "flow quantity"]
                    ]

                    res, quantity = liaison_lci(
                        flow_df,
                        year,
                        facility_id,
                        stage,
                        material,
                        unit,
                        route_id,
                        region,
                        self.liaison_process_bridge,
                        self.additional_inventories,
                        self.liaison_reeds_project_name,
                        self.liaison_reeds_database,
                        self.celavi_lca_project,
                        self.pv_module_chars,
                        str(self.data_dir),
                        verbose,
                        self.bw,
                    )

                    if not res.empty:
                        res["year"] = original_year
                        res["value"] = res["value"] / quantity
                        res.drop_duplicates(inplace=True)
                        res2 = res[['lcia','unit','year','method','stage','state','value']]
                        self.lca_database = pd.concat([self.lca_database,res2]).drop_duplicates()
                        self.lca_database.to_csv(
                            self.shortcutlca_path,
                            index=False,
                            header=False,
                        )
                        live = res.copy()
                    elif verbose:
                        logger.warning(
                            "Empty LCA result for %d, %s, %s", original_year, stage, material
                        )
                elif verbose:
                    logger.debug(
                        "Skipped live LCA: zero flow or no entries for %d, %s, %s",
                        original_year,
                        stage,
                        material,
                    )

                if not cached.empty:
                    cached = cached.assign(comment="shortcut calculations")
                    results.append(cached)
                if not live.empty:
                    live = live.assign(comment="full calculations")
                    results.append(live)

        if not results:
            return pd.DataFrame()

        final = pd.concat(results, ignore_index=True)
        final = final.assign(run=self.run_id, impacts=final["lcia"], impact=final["value"])
        cols = [
            "year",
            "facility_id",
            "material",
            "route_id",
            "stage",
            "state",
            "impacts",
            "impact",
            "unit",
            "run",
            "comment",
        ]
        final = final[cols]

        final.to_csv(self.lcia_des_path, mode="a", index=False, header=False)
        return final
