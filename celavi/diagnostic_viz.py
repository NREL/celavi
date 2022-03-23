from typing import Dict, List
from pathlib import Path
from contextlib import suppress
import pandas as pd
import numpy as np
import plotly.express as px

from .inventory import FacilityInventory


class DiagnosticViz:
    """
    This class creates diagnostic visualizations from a context after the
    model run has been executed.
    """

    def __init__(
        self,
        facility_inventories: Dict[str, FacilityInventory],
        output_plot_filename: str,
        keep_cols: List[str],
        start_year: int,
        timesteps_per_year: int,
        component_count: Dict[str, int],
        var_name: str,
        value_name: str,
        run: int,
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

        component_count : Dict[str, int]
            Dictionary where the keys are component names and the values are
            the number of components in one technology unit.

        var_name: str
            The name of the generalized var column, like 'material' or 'unit'.

        value_name: str
            The name of the generalized value column, like 'count' or 'tonnes'.

        run : int
            Model run identifier for uncertainty runs within a scenario.
        """
        self.facility_inventories = facility_inventories
        self.output_plot_filename = str.split(output_plot_filename, ".")[0] + '_' + str(run) + '.' + str.split(output_plot_filename, ".")[1]
        self.keep_cols = keep_cols
        self.start_year = start_year
        self.timestep_per_year = timesteps_per_year
        self.component_count = component_count
        self.var_name = var_name
        self.value_name = value_name
        self.run = run

        # This instance attribute is not set by a parameter to the
        # constructor. Rather, it is merely created to hold a cached
        # result from the gather_cumulative_histories() method
        # below

        self.gathered_and_melted_cumulative_histories = None

    def gather_and_melt_cumulative_histories(self) -> pd.DataFrame:
        """
        This gathers the cumulative histories in a way that they can be plotted

        Returns
        -------
        pd.DataFrame
            A dataframe with the cumulative histories gathered together.
        """
        if self.gathered_and_melted_cumulative_histories is not None:
            return self.gathered_and_melted_cumulative_histories

        cumulative_histories = []

        for facility, inventory in self.facility_inventories.items():
            cumulative_history = inventory.cumulative_history
            cumulative_history = cumulative_history.drop(columns = ['timestep'])
            cumulative_history = cumulative_history.reset_index()
            cumulative_history.rename(columns={"index": "timestep"}, inplace=True)
            facility_type, facility_id = facility.split("_")
            cumulative_history["facility_type"] = facility_type
            cumulative_history["facility_id"] = facility_id
            cumulative_history["year"] = (
                cumulative_history["timestep"] / self.timestep_per_year
            ) + self.start_year
            cumulative_history["year_floor"] = np.floor(cumulative_history["year"])
            
            # scale component counts with dictionary from config, if component
            # columns are present
            
            # Multiply component counts in the inventory by the number of
            # components in each technology unit
            with suppress(KeyError):
                cumulative_history.loc[
                    :, [key for key, value in self.component_count.items()]
                ] = cumulative_history.loc[
                    :, [key for key, value in self.component_count.items()]
                ] * [
                    value for key, value in self.component_count.items()
                ]

            cumulative_histories.append(cumulative_history)

        cumulative_histories = pd.concat(cumulative_histories)

        self.gathered_and_melted_cumulative_histories = (
            cumulative_histories.drop(["timestep", "year_floor", "facility_id"], axis=1)
            .melt(
                var_name=self.var_name,
                value_name=self.value_name,
                id_vars=["year", "facility_type"],
            )
            .groupby(["year", "facility_type", self.var_name])
            .sum()
            .reset_index()
        )

        # Add a column with the model run number
        self.gathered_and_melted_cumulative_histories['run'] = self.run

        return self.gathered_and_melted_cumulative_histories

    def generate_plots(self):
        """
        This method generates the history plots.
        """
        # Create the figure
        fig = px.line(
            self.gather_and_melt_cumulative_histories(),
            x="year",
            y=self.value_name,
            facet_row=self.var_name,
            title=self.var_name,
            color="facility_type",
            width=1000,
            height=1000,
        )

        # If a previous figure exists, remove it
        Path(self.output_plot_filename).unlink(missing_ok=True)

        # Write the figure
        fig.write_image(self.output_plot_filename)
