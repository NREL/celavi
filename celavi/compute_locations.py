import celavi.data_manager as Data
import warnings
import pandas as pd
import numpy as np

warnings.simplefilter('error', UserWarning)


class ComputeLocations:
    def __init__(self,
                 wind_turbine_locations,
                 landfill_locations,
                 other_facility_locations,
                 transportation_graph,
                 node_locations,
                 lookup_facility_type,
                 turbine_data_filename,
                 standard_scenarios_filename):

        # file paths for raw data used to compute locations
        self.wind_turbine_locations = wind_turbine_locations
        self.landfill_locations = landfill_locations
        self.other_facility_locations = other_facility_locations
        self.transportation_graph = transportation_graph
        self.node_locations = node_locations
        self.turbine_data_filename = turbine_data_filename
        self.standard_scenarios_filename = standard_scenarios_filename

        self.lookup_facility_type_file=lookup_facility_type

        # data backfill flag
        self.backfill = True

        # flag to use limited set of source data
        self.toy = False

        # Store turbine data in self for use in generating both the locations
        # file and the number_of_turbines file
        self.capacity_data = None

        self.facility_type_lookup = pd.read_csv(self.lookup_facility_type_file, header=None)


    def wind_power_plant(self):

        """Process data for wind power plants - from USWTDB"""
        turbine_locations = Data.TurbineLocations(fpath=self.wind_turbine_locations, backfill=self.backfill)
        
        # select only those turbines with eia_ids (exclude turbines without) only 9314 out of 67814 don't have eia_id
        turbine_locations_with_eia = turbine_locations[(turbine_locations['eia_id'] != '-1') &
                                                       (turbine_locations['p_year'] != '-1')]

        # reformat data for later use
        turbine_locations_with_eia.rename(columns={"t_state": "region_id_2",
                                                   "t_county": "region_id_3",
                                                   "xlong": "long",
                                                   "ylat": "lat",
                                                   "eia_id": "facility_id"},
                                          inplace=True)

        # exclude Hawaii, Guam, Puerto Rico, and Alaska (only have road network data for the contiguous United States)
        turbine_locations_with_eia = turbine_locations_with_eia[turbine_locations_with_eia.region_id_2 != 'GU']
        turbine_locations_with_eia = turbine_locations_with_eia[turbine_locations_with_eia.region_id_2 != 'HI']
        turbine_locations_with_eia = turbine_locations_with_eia[turbine_locations_with_eia.region_id_2 != 'PR']
        turbine_locations_with_eia = turbine_locations_with_eia[turbine_locations_with_eia.region_id_2 != 'AK']

        # exclude Nantucket since transport routing doesn't currently include ferries
        turbine_locations_with_eia = turbine_locations_with_eia[turbine_locations_with_eia.region_id_3 != 'Nantucket']

        # exclude Block Island since no transport from offshore turbine to shore
        turbine_locations_with_eia = turbine_locations_with_eia[turbine_locations_with_eia.facility_id != 58035]

        # Filter down the dataset to generate the number_of_turbines file
        n_turb = turbine_locations_with_eia[
            ['facility_id','p_name', 'p_year', 'p_tnum','t_model','t_cap']
        ].drop_duplicates().dropna()

        n_turb2 = n_turb[n_turb['p_year'] > 1999]
        n_turb3 = n_turb2[
            ['facility_id','p_name', 'p_year', 'p_tnum', 't_cap']
        ].drop_duplicates(
            ['facility_id','p_name', 'p_year', 'p_tnum']
        ).dropna()

        n_turb4 = n_turb3[['facility_id', 'p_year','p_name','p_tnum', 't_cap']]
        n_turb4['indicator'] = n_turb4.duplicated(subset = ['facility_id', 'p_year'],keep = False)
        n_turb4_corr = n_turb4.drop_duplicates(['facility_id', 'p_year'],keep = 'last')
        n_turb5_corr = n_turb4_corr.drop_duplicates(['p_name', 'p_year'],keep = 'last')
        n_turb5_corr['indicator'] = n_turb5_corr.duplicated(subset = ['facility_id','p_year'],keep = False)
        n_turb5_corr['n_turbine'] = n_turb5_corr['p_tnum']
        n_turb5_corr['year'] = n_turb5_corr['p_year']
        n_turb5_corr1 = n_turb5_corr[['facility_id','year','p_name','n_turbine', 't_cap']]

        # Add capacity expansion projections onto the historical data
        self.capacity_projections(n_turb5_corr1)

        turbine_locations_filtered = turbine_locations_with_eia[
            turbine_locations_with_eia.p_year > 1999
        ]

        # determine average lat and long for all turbines by facility_id
        # #(this is the plant location for each facility_id)
        plant_locations = turbine_locations_filtered[['facility_id', 'long', 'lat']].groupby(by=['facility_id']).mean().reset_index()
        plant_locations = plant_locations.astype({'facility_id': 'int'})  # recast type for facility_id
        # select turbine data for county with most capacity (some plants have turbines in multiple counties and/or
        # multiple phases with different amounts of capacity)
        plant_turbine_capacity = turbine_locations_filtered[['facility_id', 'region_id_2', 'region_id_3', 'p_cap', 't_cap']]
        plant_county_phase = plant_turbine_capacity.groupby(by=['facility_id', 'region_id_2', 'region_id_3', 'p_cap']).sum().reset_index()
        wind_plant_list = plant_county_phase.groupby(by=['facility_id', 'region_id_2']).max().reset_index()[['facility_id', 'region_id_2', 'region_id_3']]

        # merge plant list with location data
        wind_plant_locations = wind_plant_list.merge(plant_locations, on='facility_id')

        # use the number_of_turbines data structure to filter down the
        # turbine_locations_with_eia data structure
        wind_plant_locations = wind_plant_locations[
            wind_plant_locations.facility_id.isin(
                n_turb5_corr1.facility_id
            )
        ].drop_duplicates(subset='facility_id',
                          keep='first')

        wind_plant_type_lookup = self.facility_type_lookup[self.facility_type_lookup[0].str.contains('power plant')].values[0][0]
        if wind_plant_type_lookup:
            wind_plant_facility_type_convention = wind_plant_type_lookup
        else:
            warnings.warn('Wind plant facility type missing from facility_type lookup table.')

        wind_plant_locations["facility_type"] = wind_plant_facility_type_convention
        wind_plant_locations["region_id_1"] = 'USA'
        wind_plant_locations["region_id_4"] = ''
        wind_plant_locations = wind_plant_locations.astype({'facility_id': 'int'})

        return wind_plant_locations


    def landfill(self):
        """Process data for landfills - from EPA LMOP"""

        # load landfill facility data
        landfill_locations_all = Data.LandfillLocations(fpath=self.landfill_locations, backfill=self.backfill)

        # reformat landfill data
        landfill_locations_all = landfill_locations_all.rename(columns={"State": "region_id_2",
                                                                "County": "region_id_3",
                                                                "City": "region_id_4",
                                                                "Longitude": "long",
                                                                "Latitude": "lat",
                                                                "Landfill ID": "facility_id",
                                                                "Landfill Closure Year": "landfill_closure_year",
                                                                "Current Landfill Status": "current_landfill_status"
                                                                })
        landfill_locations_all = landfill_locations_all.astype({'landfill_closure_year': 'int'})

        landfill_type_lookup = self.facility_type_lookup[self.facility_type_lookup[0].str.contains('landfill')].values[0][0]
        if landfill_type_lookup:
            landfill_facility_type_convention = landfill_type_lookup
        else:
            warnings.warn('Landfill facility type missing from facility_type lookup table.')

        landfill_locations_all["facility_type"] = landfill_facility_type_convention
        landfill_locations_all["region_id_1"] = 'USA'

        # select only open landfills
        landfill_locations = landfill_locations_all[landfill_locations_all['current_landfill_status'] == 'Open']
        landfill_locations = landfill_locations[['facility_id', 'facility_type', 'long', 'lat', 'region_id_1', 'region_id_2', 'region_id_3', 'region_id_4']]

        # drop landfills that have null values for lat and long
        # (data cleanup from LMOP data; 7 cases where landfills exist but no locations are defined; e.g., facility_id = 2173)
        landfill_locations_no_nulls = landfill_locations.dropna(subset=['long', 'lat'])

        return landfill_locations_no_nulls

    def other_facility(self):
        """Process other facility data"""

        facility_locations = Data.OtherFacilityLocations(fpath=self.other_facility_locations, backfill=self.backfill)

        number_other_facilities = len(facility_locations)
        number_unique_facility_id = len(facility_locations.facility_id.unique())

        list_other_facility_types = facility_locations.facility_type.unique()

        for facility_type in list_other_facility_types:
            other_facility_type_lookup = self.facility_type_lookup[self.facility_type_lookup[0].str.contains(facility_type)].values[0][0]

            if other_facility_type_lookup:
                facility_locations = facility_locations.replace({'facility_type': facility_type},
                                                                {'facility_type': other_facility_type_lookup},
                                                                regex=True)
            else:
                warnings.warn('Facility type missing from facility_type lookup table.')


        if number_other_facilities != number_unique_facility_id:
            warning_str = "The facility_id column in other facility locations is not unique - " \
                          "please verify your input file is correctly generated. Number facilities is %d; " \
                          "number unique faclity_id is %d." % (number_other_facilities, number_unique_facility_id)
            warnings.warn(warning_str)
        return facility_locations

    def capacity_projections(self, capacity_data):
        """
        Parameters
        ----------
        capacity_data

        Returns
        -------
        None
        """
        raise NotImplementedError
        # Read in the standard scenario data
        stscen = Data.StandardScenarios(fpath=self.standard_scenarios_filename,
                                        backfill=self.backfill).rename(columns={'t':'year'})

        # group stscen by state and take the consecutive difference of the
        # capacity column
        stscen['cap_new'] = stscen.groupby('state')['wind-ons_MW'].diff()

        # where total capacity decreases in a year, set the new capacity value
        # to 0
        stscen['cap_new'][stscen['cap_new'] < 0] = 0

        # .diff() leaves empty values where there is no previous row.
        # replace these NAs with 0
        stscen.fillna(value=0, inplace=True)

        # capacity_data is historical
        # find the average turbine capacity, weighted by number of turbines,
        # in each year up to the present day
        avg_cap_hist = capacity_data.groupby(
            by='year'
        ).apply(
            lambda x: np.average(x.t_cap, weights=x.n_turbine)
        ).reset_index(
        ).rename(
            columns={0:'avg_t_cap'}
        )

        joined = stscen.join(avg_cap_hist, on='year', how='left')


    def join_facilities(self, locations_output_file):
        """Join all facility data into single file"""

        wind_plant_locations = ComputeLocations.wind_power_plant(self)
        landfill_locations_no_nulls = ComputeLocations.landfill(self)
        facility_locations = ComputeLocations.other_facility(self)

        locations = facility_locations.append(wind_plant_locations)
        locations = locations.append(landfill_locations_no_nulls)
        locations.reset_index(drop=True, inplace=True)

        # find the entries in locations that have a duplicate facility_id AND
        # are not power plants.
        _ids_update = locations[locations.duplicated(subset='facility_id',
                                                     keep=False)]
        _ids_update = _ids_update.loc[_ids_update.facility_type != 'power plant'].index

        # Update the facility_id values for these entries in the locations data
        # frame.
        for i in _ids_update:
            locations.loc[i, 'facility_id'] = int(max(locations.facility_id) + 1)
        
        locations.to_csv(locations_output_file, index=False)


