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
        output_plot_filename: str,
        keep_cols: List[str],
        start_year: int,
        timesteps_per_year: int,
    ):
        """
        Parameters
        ----------
        facility_inventories: Dict[str, FacilityInventory]
            The dictionary of facility inventories from the Context

        output_plot_filename: str
            The absolute path to the filename that will hold the final
            generated plot.

        keep_cols: List[str]
            This is a list of the possible material names (for material
            facility inventories) or a list of the possible component names
            (for count facility inventories)

        start_year: int
            The start year for the DES model.

        timesteps_per_year: int
            The timesteps per year for the DES model.
        """
        self.facility_inventories = facility_inventories
        self.output_plot_filename = output_plot_filename
        self.keep_cols = keep_cols
        self.start_year = start_year
        self.timestep_per_year = timesteps_per_year

        # This instance attribute is not set by a parameter to the
        # constructor. Rather, it is merely created to hold a cached
        # result from the gather_cumulative_histories() method
        # below

        self.cumulative_histories = None

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
            cumulative_history["year"] = (
                cumulative_history["timestep"] / self.timestep_per_year
            ) + self.start_year
            cumulative_history["year_ceil"] = np.ceil(cumulative_history["year"])
            cumulative_histories.append(cumulative_history)

        self.cumulative_histories = pd.concat(cumulative_histories)

        return self.cumulative_histories

    def generate_plots(self, var_name: str, value_name: str):
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
        # for either mass or count plots, and sum over years and facility types.
        melted_and_grouped = (
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
            melted_and_grouped,
            x="year",
            y=value_name,
            facet_row=var_name,
            title=var_name,
            color="facility_type",
            width=1000,
            height=1000,
        )

        # Write the figure
        fig.write_image(self.output_plot_filename)
