from typing import Dict, List

import os

import pandas as pd
import numpy as np
import plotly.express as px
import time

from .inventory import FacilityInventory


class DiagnosticVizAndDataFrame:
    """
    This class creates diagnostic visualizations from a context when after the
    model run has been executed.
    """

    def __init__(
        self,
        facility_inventories: Dict[str, FacilityInventory],
        units: str,
        output_folder_path: str,
        keep_cols: List[str],
    ):
        """
        Parameters
        ----------
        facility_inventories: Dict[str, FacilityInventory]
            The dictionary of facility inventories from the Context

        units: str
            The units in the referenced facility inventories.

        output_folder_path: str
            The folder where the plots will show up.
        """
        self.facility_inventories = facility_inventories
        self.cumulative_histories = None
        self.units = units
        self.output_folder_path = output_folder_path
        self.keep_cols = keep_cols

    def gather_cumulative_histories(self) -> pd.DataFrame:
        """
        This gathers the cumulative histories in a way that they can be plotted

        Returns
        -------
        pd.DataFrame
            A dataframe with the cumulative histories gathered together.
        """
        if self.cumulative_histories is not None:
            return self.cumulative_histories

        cumulative_histories = []

        for facility, inventory in self.facility_inventories.items():
            cumulative_history = inventory.cumulative_history
            cumulative_history = cumulative_history.reset_index()
            cumulative_history.rename(columns={"index": "timestep"}, inplace=True)
            facility_type, facility_id = facility.split("_")
            cumulative_history["facility_type"] = facility_type
            cumulative_history["facility_id"] = facility_id
            cumulative_history["year"] = (cumulative_history["timestep"] / 12) + 2000
            cumulative_history["year_ceil"] = np.ceil(cumulative_history["year"])
            cumulative_histories.append(cumulative_history)

        self.cumulative_histories = pd.concat(cumulative_histories)

        return self.cumulative_histories

    def generate_plots(self, var_name: str, value_name: str) -> pd.DataFrame:
        """
        This method generates the history plots.

        Parameters
        ----------
        var_name: str
            The name of the generalized var column, like 'material' or 'unit'.

        value_name: str
            The name of the generalized value column, like 'count' or 'tonnes'.
        """
        # First, melt the dataframe so that its data structure is generalized
        # for either count or mass plots.
        molten = (
            self.gather_cumulative_histories()
            .drop(["timestep", "year_ceil", "facility_id"], axis=1)
            .melt(
                var_name=var_name,
                value_name=value_name,
                id_vars=["year", "facility_type"],
            )
            .groupby(["year", "facility_type", var_name])
            .sum()
            .reset_index()
        )

        # Create the figure
        fig = px.line(
            molten,
            x="year",
            y=value_name,
            facet_row=var_name,
            title=var_name,
            color="facility_type",
            width=1000,
            height=1000,
        )

        # Create the output filename
        facet_plots_filename = os.path.join(
            self.output_folder_path, f"{var_name}_facets.png"
        )

        # Write the figure
        fig.write_image(facet_plots_filename)

        return molten
