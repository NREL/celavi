import pandas as pd



def data_filter(loc_file_name,num_of_turbines_filename,states):

        locations = pd.read_csv(loc_file_name)
        
        selected_states = states
        
        locations_filtered = locations[locations['region_id_2'].isin(selected_states)]
        locations_filtered.to_csv(loc_file_name)
        
        facililites_included = locations_filtered[['facility_id', 'facility_type', 'lat', 'long']]
        facility_id_included = list(pd.unique(facililites_included['facility_id']))

        number_of_turbines = pd.read_csv(num_of_turbines_filename)
        number_of_turbines_filtered = number_of_turbines[number_of_turbines['facility_id'].isin(facility_id_included)]
        number_of_turbines_filtered.to_csv(num_of_turbines_filename)
