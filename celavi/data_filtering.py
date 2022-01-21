import pandas as pd


def filter_locations(loc_filename,
                     tech_units_filename,
                     states):
        """
        This function is used to filter facility and technology unit locations
        based on the list of states to include provided in the
        scenario-specific config file.

        The filtered datasets overwrite the original datasets (CSV files).


        Parameters
        ----------
        loc_filename: str
            Path to the unfiltered computed locations dataset.
        
        tech_units_filename: str
            Path to the unfiltered number of technology units dataset.
        
        states: list
            List of states to include in the filtered datasets.

        Returns
        -------
        None
        """

        locations = pd.read_csv(loc_filename)

        selected_states = states

        locations_filtered = locations[locations['region_id_2'].isin(selected_states)]
        locations_filtered.to_csv(loc_filename)

        facililites_included = locations_filtered[['facility_id', 'facility_type', 'lat', 'long']]
        facility_id_included = list(pd.unique(facililites_included['facility_id']))

        num_tech_units = pd.read_csv(tech_units_filename)
        num_tech_units_filter = num_tech_units[num_tech_units['facility_id'].isin(facility_id_included)]
        num_tech_units_filter.to_csv(tech_units_filename)


def filter_routes(filtered_locations_filename, routes_filename):
        """
        This function is used to filter the routes file such that only routes
        with both the source and destination contained within the states
        specified in the scenario config file are included. Routes that
        originate, terminate, or both outside the specified states are removed
        from the dataset.

        The filtered routes dataset overwrites the original routes dataset
        (CSV file).


        Parameters
        ----------
        filtered_locations_filename: str
            Path to the locations dataset that was previously filtered by state
            using the filter_locations method.
        
        routes_filename: str
            Path to the unfiltered routes dataset. Either the computed routes
            dataset provided by the Router or a custom routes dataset may be
            used.
        
        Returns
        -------
        None
        """

        facility_id_included = list(
                pd.read_csv(filtered_locations_filename).facility_id.unique()
        )

        routes = pd.read_csv(routes_filename)

        routes_filtered = routes[(routes.source_facility_id.isin(facility_id_included)) &
                                 (routes.destination_facility_id.isin(facility_id_included))].drop_duplicates()

        routes_filtered.to_csv(routes_filename)
