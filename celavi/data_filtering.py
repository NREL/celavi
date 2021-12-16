# TODO: Add a short module docstring above the code to:
#  1) provide authors, date of creation
#  2) give a high level description (2-3 lines) of what the module does
#  3) write any other relevant information

import pandas as pd


def filter_locations(loc_file_name, num_of_turbines_filename, states):
        # TODO: add docstrings to explain input variables and what the function
        #  does.

        locations = pd.read_csv(loc_file_name)

        selected_states = states

        locations_filtered = locations[locations['region_id_2'].isin(selected_states)]
        locations_filtered.to_csv(loc_file_name)

        facililites_included = locations_filtered[['facility_id', 'facility_type', 'lat', 'long']]
        facility_id_included = list(pd.unique(facililites_included['facility_id']))

        number_of_turbines = pd.read_csv(num_of_turbines_filename)
        number_of_turbines_filtered = number_of_turbines[number_of_turbines['facility_id'].isin(facility_id_included)]
        number_of_turbines_filtered.to_csv(num_of_turbines_filename)


def filter_routes(locations_filename, routes_filename):
        # TODO: add docstrings to explain input variables and what the function
        #  does.
        """

        """

        facility_id_included = list(
                pd.read_csv(locations_filename).facility_id.unique()
        )

        routes = pd.read_csv(routes_filename)

        routes_filtered = routes[(routes.source_facility_id.isin(facility_id_included)) &
                                 (routes.destination_facility_id.isin(facility_id_included))].drop_duplicates()

        routes_filtered.to_csv(routes_filename)
