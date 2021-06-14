import data_manager as Data
import warnings
import pandas as pd
import pdb
warnings.simplefilter('error', UserWarning)


class ComputeLocations:
    def __init__(self):
        # file paths for raw data used to compute locations
        self.wind_turbine_locations = '../../celavi-data/inputs/raw_location_data/uswtdb_v3_3_20210114.csv'  # wind turbine locations using USWTDB format
        self.landfill_locations = '../../celavi-data/inputs/raw_location_data/landfilllmopdata.csv' # LMOP data for landfill locations
        self.other_facility_locations = '../../celavi-data/inputs/raw_location_data/other_facility_locations_all_us.csv'  # other facility locations (e.g., cement)
        self.transportation_graph = '../../celavi-data/inputs/precomputed_us_road_network/transportation_graph.csv'  # transport graph (pre computed; don't change)
        self.node_locations = '../../celavi-data/inputs/precomputed_us_road_network/node_locations.csv'  # node locations for transport graph (pre computed; don't change)

        # data backfill flag
        self.backfill = True

        # flag to use limited set of source data
        self.toy = False

        self.lookup_facility_type_file = '../../celavi-data/lookup_tables/facility_type.csv'
        self.facility_type_lookup = pd.read_csv(self.lookup_facility_type_file, header=None)

        self.lookup_facility_id = '../../celavi-data/lookup_tables/facility_id.csv'
        self.facility_id_lookup = pd.read_csv(self.lookup_facility_id, header=None)

    def wind_power_plant(self):
        """Process data for wind power plants - from USWTDB"""

        turbine_locations = Data.TurbineLocations(fpath=self.wind_turbine_locations, backfill=self.backfill)

        # select only those turbines with eia_ids (exclude turbines without) only 9314 out of 67814 don't have eia_id
        turbine_locations_with_eia = turbine_locations[turbine_locations['eia_id'] != '-1']

        # determine average lat and long for all turbines by eia_id (this is the plant location for each eia_id)
        plant_locations = turbine_locations_with_eia[['eia_id', 'xlong', 'ylat']].groupby(by=['eia_id']).mean().reset_index()
        plant_locations = plant_locations.astype({'eia_id': 'int'})  # recast type for eia_id
        # select turbine data for county with most capacity (some plants have turbines in multiple counties and/or
        # multiple phases with different amounts of capacity)
        plant_turbine_capacity = turbine_locations_with_eia[['eia_id', 't_state', 't_county', 'p_cap', 't_cap']]
        plant_county_phase = plant_turbine_capacity.groupby(by=['eia_id', 't_state', 't_county', 'p_cap']).sum().reset_index()
        wind_plant_list = plant_county_phase.groupby(by=['eia_id', 't_state']).max().reset_index()[['eia_id', 't_state', 't_county']]

        # merge plant list with location data and reformat data for use
        wind_plant_locations = wind_plant_list.merge(plant_locations, on='eia_id')
        wind_plant_locations = wind_plant_locations.rename(columns={"t_state": "region_id_2",
                                                                    "t_county": "region_id_3",
                                                                    "xlong": "long",
                                                                    "ylat": "lat",
                                                                    "eia_id": "facility_id"})

        # if there are still duplicate facility_id values, keep only the first
        # entry with that value and drop the rest
        wind_plant_locations.drop_duplicates(subset='facility_id',keep='first',
                                             inplace=True)

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

    def join_facilities(self, locations_output_file):
        """Join all facility data into single file"""

        wind_plant_locations = ComputeLocations.wind_power_plant(self)
        landfill_locations_no_nulls = ComputeLocations.landfill(self)
        facility_locations = ComputeLocations.other_facility(self)

        locations = facility_locations.append(wind_plant_locations)
        locations = locations.append(landfill_locations_no_nulls)
        locations.reset_index(drop=True, inplace=True)

        # exclude Hawaii, Guam, Puerto Rico, and Alaska (only have road network data for the contiguous United States)
        locations = locations[locations.region_id_2 != 'GU']
        locations = locations[locations.region_id_2 != 'HI']
        locations = locations[locations.region_id_2 != 'PR']
        locations = locations[locations.region_id_2 != 'AK']

        # exclude Nantucket since transport routing doesn't currently include ferries
        locations = locations[locations.region_id_3 != 'Nantucket']

        # exclude Block Island since no transport from offshore turbine to shore
        locations = locations[locations.facility_id != 58035]

        # find the entries in locations that have a duplicate facility_id AND
        # are not power plants.
        _ids_update = locations[locations.duplicated(subset='facility_id',keep=False)]
        _ids_update = _ids_update.loc[_ids_update.facility_type != 'power plant'].index

        # Update the facility_id values for these entries
        # in the locations data frame.
        for i in _ids_update:
            locations.loc[i, 'facility_id'] = int(max(locations.facility_id) + 1)
        
        locations.to_csv(locations_output_file, index=False)
