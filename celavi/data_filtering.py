import pandas as pd


def filter_locations(loc_file_name,num_of_turbines_filename,states):
        
        """
        This function is used to filter the locations file and number of turbines file
        based on the states selected for filtering.
        After filtering the location and number of turbines file it rewrites and
        saves the csv files


        Parameters
        ----------
        loc_file_name: str
            file name for the location file
        
        num_of_turbines_filename: str
            file name for the number of turbines file based on facility id. 
        
        states: list
            list for the states for filtering

        
        Returns
        -------
        None
        """

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
        """
        This function is used to filter the routes file.        
        After filtering the routes file it rewrites and
        saves as csv files


        Parameters
        ----------
        locations_fil_name: str
            file name for the location file
        
        routes_filename: str
            file name for the routes file. 

        
        Returns
        -------
        None
        """

        facility_id_included = list(
                pd.read_csv(locations_filename).facility_id.unique()
        )

        routes = pd.read_csv(routes_filename)

        routes_filtered = routes[(routes.source_facility_id.isin(facility_id_included)) &
                                 (routes.destination_facility_id.isin(facility_id_included))].drop_duplicates()

        routes_filtered.to_csv(routes_filename)
