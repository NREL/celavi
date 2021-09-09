import os

import pandas as pd
import numpy as np
import plotly.express as px

from .des import Context


class DiagnosticViz:
    """
    This class creates diagnostic visualizations from a context when after the
    model run has been executed.
    """

    def __init__(self, context: Context, output_folder_path: str):
        self.context = context
        self.cumulative_histories = None
        self.output_folder_path = output_folder_path

    def gather_cumulative_histories(self) -> pd.DataFrame:
        cumulative_histories = []

        for facility, inventory in self.context.count_facility_inventories.items():
            cumulative_history = inventory.cumulative_history
            cumulative_history = cumulative_history.reset_index()
            cumulative_history.rename(columns={'index': 'timestep'}, inplace=True)
            facility_type, facility_id = facility.split("_")
            cumulative_history['facility_type'] = facility_type
            cumulative_history['facility_id'] = facility_id
            cumulative_history['year'] = (cumulative_history['timestep'] / 12) + 2000
            cumulative_history['year_ceil'] = np.ceil(cumulative_history['year'])
            cumulative_histories.append(cumulative_history)

        gathered = pd.concat(cumulative_histories)

        blades_only = gathered.drop(columns=['nacelle', 'tower', 'foundation'])
        blades_only.rename(columns={'blade': 'blade_count'}, inplace=True)

        return blades_only

    def generate_blade_count_plots(self):
        cumulative_histories = self.gather_cumulative_histories()
        blade_counts = cumulative_histories.loc[:, ['year', 'blade_count', 'facility_type']].groupby(
            ['year', 'facility_type']).sum().reset_index()
        fig = px.line(blade_counts, x='year', y='blade_count', facet_col='facility_type', title='Blade Counts',
                      facet_col_wrap=2, width=1000, height=1500)
        facet_plots_filename = os.path.join(self.output_folder_path, "blade_count_facets.png")
        fig.write_image(facet_plots_filename)
        blade_counts = cumulative_histories.loc[:, ['year', 'blade_count', 'facility_type']].groupby(
            ['year', 'facility_type']).sum().reset_index()
        fig = px.line(blade_counts, x='year', y='blade_count', color='facility_type', title='Blade Counts', width=1000,
                      height=500)
        one_plot_filename = os.path.join(self.output_folder_path, "blade_count_single.png")
        fig.write_image(one_plot_filename)
