from typing import Dict, List
from pathlib import Path
from contextlib import suppress
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex

from .inventory import FacilityInventory


class DiagnosticViz:
    """
    Create basic diagnostic visualizations from a Context instance after the
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
        raw_cumulative_histories_file: str,
        component_scaledown: int = None,
    ):
        """
        Define class attributes.

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
        
        raw_cumulative_histories_file : str
            Filepath where the un-process cumulative histories data is saved.

        component_scaledown: int or None, Default = None
            Multiplier used to scale up component counts - used for these basic
            visualizations ONLY.
        """
        self.facility_inventories = facility_inventories
        _name, _ext = str.split(output_plot_filename, ".")
        self.output_plot_filename = f'{_name}_{run}.{_ext}'
        self.keep_cols = keep_cols
        self.start_year = start_year
        self.timestep_per_year = timesteps_per_year
        self.component_count = component_count
        self.var_name = var_name
        self.value_name = value_name
        self.run = run

        self.component_scaledown = component_scaledown

        # Create blank attribute to hold results from gather_cumulative_histories() method
        self.gathered_and_melted_cumulative_histories = None

        self.raw_cumulative_histories_file = raw_cumulative_histories_file


    def gather_and_melt_cumulative_histories(self) -> pd.DataFrame:
        """
        Gather and rearrange the cumulative histories from every facility
        to allow for plotting component counts.

        Parameters
        ----------
        None

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
                    :, [key for key, _ in self.component_count.items()]
                ] = cumulative_history.loc[
                    :, [key for key, _ in self.component_count.items()]
                ] * [
                    value for _, value in self.component_count.items()
                ]

            cumulative_histories.append(cumulative_history)

        # Fill any empty entries (generally where a facility never processed a
        # particular component kind) with zeros
        cumulative_histories_df = pd.concat(cumulative_histories).fillna(0)

        # Save a raw version of the histories file for debugging
        cumulative_histories_df.to_csv(self.raw_cumulative_histories_file,index=False)

        self.gathered_and_melted_cumulative_histories = (
            cumulative_histories_df.drop(["timestep", "year_floor", "facility_id"], axis=1)
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
        Generate component mass and counts over time with Plotly Express.

        Plots are saved to file.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # Create the figure
        _colors = plt.cm.jet(np.linspace(0,1,len(self.gather_and_melt_cumulative_histories().facility_type.drop_duplicates())))
        _factypes = self.gather_and_melt_cumulative_histories().facility_type.drop_duplicates().values
        color_fac = {}
        for fac, col in zip(_factypes, _colors): color_fac[fac] = to_hex(col)
        fig = px.line(
            self.gather_and_melt_cumulative_histories(),
            x="year",
            y=self.value_name,
            facet_row=self.var_name,
            title=self.var_name,
            color="facility_type",
            color_discrete_map = color_fac,
            width=1000,
            height=1000,
        )

        if self.component_scaledown is not None:
            fig.update_layout(
                yaxis_title=f'Count ({self.component_scaledown}s of units)',
                yaxis2_title=f'Count ({self.component_scaledown}s of units)'
            )

        # If a previous figure exists, remove it
        Path(self.output_plot_filename).unlink(missing_ok=True)

        # Write the figure
        fig.write_image(self.output_plot_filename)
