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

    def __init__(self,
                 facility_inventories: Dict[str, FacilityInventory],
                 units: str,
                 output_folder_path: str,
                 keep_cols: List[str]):
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

    # def generate_plots(self):
    #     """
    #     Generate the blade count history plots
    #     """
    #     cumulative_histories = self.gather_cumulative_histories()
    #     blade_counts = (
    #         cumulative_histories.loc[:, ["year", self.units, "facility_type"]]
    #         .groupby(["year", "facility_type"])
    #         .sum()
    #         .reset_index()
    #     )
    #     fig = px.line(
    #         blade_counts,
    #         x="year",
    #         y=self.units,
    #         facet_col="facility_type",
    #         title=self.units,
    #         facet_col_wrap=2,
    #         width=1000,
    #         height=1500,
    #     )
    #     facet_plots_filename = os.path.join(
    #         self.output_folder_path, f"{self.units}_facets.png"
    #     )
    #     fig.write_image(facet_plots_filename)
    #     blade_counts = (
    #         cumulative_histories.loc[:, ["year", self.units, "facility_type"]]
    #         .groupby(["year", "facility_type"])
    #         .sum()
    #         .reset_index()
    #     )
    #     fig = px.line(
    #         blade_counts,
    #         x="year",
    #         y=self.units,
    #         color="facility_type",
    #         title=self.units,
    #         width=1000,
    #         height=500,
    #     )
    #     one_plot_filename = os.path.join(
    #         self.output_folder_path, f"{self.units}_single.png"
    #     )
    #     fig.write_image(one_plot_filename)
