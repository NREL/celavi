import pandas as pd
import os

filepath = 'data/outputs/'
state_list = ['AL', 'AR', 'AZ', 'CA', 'FL', 'GA', 'IA', 'ID', 'IL', 'IN', 'KS',
              'KY', 'MD', 'ME', 'MI', 'MO', 'MT', 'NC', 'NE', 'NJ', 'NM', 'NV',
              'NY', 'OH', 'OK', 'OR', 'PA', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA',
              'WA', 'CO', 'WY', 'MN', 'VT', 'MA', 'WI', 'WV', 'ND', 'NH', 'DE',
              'RI', 'CT', 'LA', 'MS', 'VI']

file_name = 'route_list_output_'
file_extn = '.csv'

file_list = [file_name + state + file_extn for state in state_list]

data_complete = pd.DataFrame()
for file in file_list:
    filepath_file = os.path.join(filepath, file)
    print(filepath_file)
    data = pd.read_csv(filepath_file)
    data_complete = data_complete.append(data)

data_complete.to_csv('compiled_national_routes_all_states.csv')