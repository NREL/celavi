
import celavi.data_manager as Data
import warnings
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

warnings.simplefilter('error', UserWarning)


class ComputeLocations:
    """
    The ComputeLocations class performs preprocessing that ingests raw facility
     location data and returns a formatted, aggregated dataset of all
     facilities involved in a circular supply chain.

     The specific preprocessing steps will need to be adjusted for different
     raw data sources to allow for variations in column names, data types, and
     the number of files ingested. The output format of the processed dataset
     must remain as it is defined in this code for the remainder of the CELAVI
     code base to function.
    """

    def __init__(self,
                 wind_turbine_locations,
                 landfill_locations,
                 other_facility_locations,
                 transportation_graph,
                 node_locations,
                 lookup_facility_type,
                 turbine_data_filename,
                 standard_scenarios_filename):
        """
        Parameters
        ----------
        power_plant_locations
            Data set of renewable energy power plant locations including lat,
            long, region identifier columns, and other power-plant-specific
            information as needed.

        landfill_locations
            Data set of landfills in the contiguous US.

        other_facility_locations
            Data set of all other facility types involved in the case study.

        transportation_graph
            Network of all roads in the contiguous US.

        node_locations


        lookup_facility_type
            File defining the allowable set of facility types in the case study.

        technology_data_filename
            File with technology-specific installation data, including year
            installed, location (lat, long, and region identifiers), and any
            technology-specific data required to model material flows into
            power plants.

        standard_scenarios_filename
            File of output from NREL's REEDS model, used for capacity expansion
            projections past the current year.
        """

        # file paths for raw data used to compute locations
        self.wind_turbine_locations = wind_turbine_locations
        self.landfill_locations = landfill_locations
        self.other_facility_locations = other_facility_locations
        self.transportation_graph = transportation_graph
        self.node_locations = node_locations
        self.turbine_data_filename = turbine_data_filename
        self.standard_scenarios_filename = standard_scenarios_filename

        self.lookup_facility_type_file = lookup_facility_type

        # data backfill flag
        self.backfill = True

        # flag to use limited set of source data
        self.toy = False

        # Create place to store turbine data in self for use in generating
        # the number_of_turbines file with capacity expansion
        self.capacity_data = None

        # Create place to store final locations df for use in capacity expansion
        self.locs = None

        self.facility_type_lookup = pd.read_csv(self.lookup_facility_type_file, header=None)


    def wind_power_plant(self):
        """
        Ingests raw data from the U.S. Wind Turbine database, filters down to
        the contiguous U.S. and creates a data frame that can be combined with
        other sets of facility location data.
        """

        # Process data for wind power plants - from USWTDB
        turbine_locations = Data.TurbineLocations(fpath=self.wind_turbine_locations, backfill=self.backfill)
        
        # select only those turbines with eia_ids (exclude turbines without) only 9314 out of 67814 don't have eia_id
        turbine_locations_with_eia = turbine_locations[(turbine_locations['eia_id'] != '-1') &
                                                       (turbine_locations['p_year'] != '-1')]

        # reformat data for later use
        turbine_locations_with_eia.rename(columns={"t_state": "region_id_2",
                                                   "t_county": "region_id_3",
                                                   "xlong": "long",
                                                   "ylat": "lat",
                                                   "eia_id": "facility_id",
                                                   "p_year": "year"},
                                          inplace=True)

        # TODO: why replacing self-explanatory names with non self-explanatory
        #  ones? why not replacing t_state by state and t_county by county for
        #  instance. Consider refactor region_id_1, region_id_2, region_id_3
        #  and region_id_4 by self-explanatory variable names in the all
        #  project. Also, could the exclusions below linked to considering only
        #  road transportation in the contiguous US be generalized?
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
            ['facility_id', 'p_name', 'year', 'p_tnum', 't_model', 't_cap']
        ].drop_duplicates().dropna()

        n_turb2 = n_turb[n_turb['year'] > 1999]

        # Rename the p_tnum column to n_turbine
        data3 = n_turb2.groupby(['year', 'facility_id', 'p_name', 't_cap']).size().reset_index().rename(columns={0: 'n_turbine'})
        data4 = data3.groupby(['year', 'facility_id']).apply(lambda x: np.average(x.t_cap, weights=x.n_turbine)).reset_index().rename(columns={0: 't_cap'})
        data5 = data3.groupby(['year', 'facility_id'])['n_turbine'].agg('sum').reset_index()
        data6 = data5.merge(data4, on=['year', 'facility_id'])


        # Store this dataframe into self for use in capacity projection
        # calculations
        # this file created the number of turbines file.
        self.capacity_data = data6

        turbine_locations_filtered = turbine_locations_with_eia[
            turbine_locations_with_eia.year > 1999
        ]


        # determine average lat and long for all turbines by facility_id
        # (this is the plant location for each facility_id)
        plant_locations = turbine_locations_filtered.groupby(['facility_id', 'region_id_2', "region_id_3"])['long', 'lat'].agg('mean').reset_index()
        # Dropping duplicates on p year and eia id and keeping only the first county occurences in case spread over multiple counties. Assumption
        plant_locations = plant_locations.drop_duplicates(subset=['facility_id'], keep='first')
        plant_locations = plant_locations.astype({'facility_id': 'int'})  # recast type for facility_id
        # Unique eia id and p _year have only one lat long associated now along with one region county and state.
        
        wind_plant_locations = plant_locations
        # use the number_of_turbines data structure to filter down the
        # turbine_locations_with_eia data structure
        wind_plant_locations = wind_plant_locations[
            wind_plant_locations.facility_id.isin(
                data6.facility_id
            )
        ].drop_duplicates(subset='facility_id',
                          keep='first')

        # TODO: because quite similar bits of codes are used several times
        #  and that warnings are pretty similar as well, consider writing a
        #  method to handle lookup for the wind_power_plant, landfills, and
        #  other_facility. The method would take one of the type as input and
        #  return the lookup or output a warning.
        wind_plant_type_lookup = self.facility_type_lookup[self.facility_type_lookup[0].str.contains('power plant')].values[0][0]
        if wind_plant_type_lookup:
            wind_plant_facility_type_convention = wind_plant_type_lookup
            wind_plant_locations["facility_type"] = wind_plant_facility_type_convention
        else:
            warnings.warn('Wind plant facility type missing from facility_type lookup table.')

        wind_plant_locations["region_id_1"] = 'USA'
        wind_plant_locations["region_id_4"] = ''
        wind_plant_locations = wind_plant_locations.astype({'facility_id': 'int'})

        return wind_plant_locations


    def landfill(self):
        """
        Process data for landfills - from EPA LMOP
        """

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

        # TODO: because quite similar bits of codes are used several times
        #  and that warnings are pretty similar as well, consider writing a
        #  method to handle lookup for the wind_power_plant, landfills, and
        #  other_facility. The method would take one of the type as input and
        #  return the lookup or output a warning.
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
        """
        Process other facility data
        """

        facility_locations = Data.OtherFacilityLocations(fpath=self.other_facility_locations, backfill=self.backfill)

        number_other_facilities = len(facility_locations)
        number_unique_facility_id = len(facility_locations.facility_id.unique())

        list_other_facility_types = facility_locations.facility_type.unique()

        # TODO: because quite similar bits of codes are used several times
        #  and that warnings are pretty similar as well, consider writing a
        #  method to handle lookup for the wind_power_plant, landfills, and
        #  other_facility. The method would take one of the type as input and
        #  return the lookup or output a warning.
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
                          "number unique facility_id is %d." % (number_other_facilities, number_unique_facility_id)
            warnings.warn(warning_str)
        return facility_locations

    def capacity_projections(self):
        """
        Parameters
        ----------

        Returns
        -------
        None
        """

        # Read in the standard scenario data
        stscen = Data.StandardScenarios(
            fpath=self.standard_scenarios_filename,
            backfill=self.backfill
        ).rename(
            columns={'t': 'year'}
        )

        # group stscen by state and take the consecutive difference of the
        # capacity column
        stscen['cap_new'] = stscen.groupby('state')['wind-ons_MW'].diff()

        # convert MW to kW to match the US WTDB turbine capacity data
        stscen.cap_new = stscen.cap_new * 1000.0

        # where total capacity decreases in a year, set the new capacity value
        # to 0
        stscen['cap_new'][stscen['cap_new'] < 0] = 0

        # .diff() leaves empty values where there is no previous row.
        # replace these NAs with 0
        stscen.fillna(value=0, inplace=True)

        # capacity_data is historical
        # find the average turbine capacity, weighted by number of turbines,
        # in each year up to the present day
        avg_cap_hist = self.capacity_data.groupby(
            by='year'
        ).apply(
            lambda x: np.average(x.t_cap, weights=x.n_turbine)
        ).reset_index(
        ).rename(
            columns={0: 'avg_t_cap'}
        )

        # perform a linear regression of avg_t_cap on year
        avg_t_cap_reg = LinearRegression(
        ).fit(
            np.array(avg_cap_hist.year).reshape(-1, 1),
            np.array(avg_cap_hist.avg_t_cap).reshape(-1, 1)
        )

        # extrapolate the linear regression to generate values every 2 years
        # from 2022 to 2050
        predictions = [
            [year, avg_t_cap_reg.predict(
             np.array(
                [[year]]
             )
        )[0][0]] for year in np.arange(2022, 2052, 2)
        ]

        # format extrapolations into DataFrame
        avg_cap_pred = pd.DataFrame(
            data=predictions,
            columns=['year', 'avg_t_cap']
        )

        # merge the average capacity extrapolation with the standard scenario
        # data by year
        # keep only the columns required to calculate the number of new
        # turbines
        joined = avg_cap_pred.merge(
            stscen[stscen.year > 2020],
            on='year',
            how='outer',
            suffixes=('avgcap', 'stdscen'),
            sort=True
        )[['year', 'state', 'avg_t_cap', 'cap_new']].rename(
            columns={'avg_t_cap': 't_cap'}
        )

        # calculate the number of new turbines by dividing the new capacity
        # addition with the average turbine capacity
        # round up to the nearest integer to deal in whole numbers of turbines
        joined['n_turbine'] = np.ceil(joined.cap_new / joined.t_cap)

        # remove any entries where no new turbines are installed
        joined = joined[joined.n_turbine > 0]

        # generate project names for the future capacity
        joined['p_name'] = joined.state + '_future_cap'

        # remove columns no longer needed
        capacity_future = joined[['year', 'p_name', 'n_turbine', 't_cap']]

        # Use the computed locations dataset to generate unique facility_id
        # values for these future "power plants"
        _facility_id_start = int(self.locs.facility_id.max() + 1)

        # generate a list of new facility IDs
        _new_facility_id = list(
            _facility_id_start +
            np.arange(len(capacity_future.p_name.unique()))
        )

        # create a data frame of new facility IDs and project names,
        # for merging
        _new_facility_id = pd.DataFrame(
            data={
                'p_name': list(capacity_future.p_name.unique()),
                'facility_id': _new_facility_id
            }
        )

        # merge to add a facility_id column to the capacity projection data
        capacity_future = capacity_future.merge(
            _new_facility_id[['p_name', 'facility_id']],
            on='p_name',
            how='outer'
        )

        # TODO: it seems that the "turbine_data_filename.csv" is an
        #  intermediary output that is used as an input later. In the config
        #  file it is listed as an input. Consider clarifying the role of
        #  "turbine_data_filename.csv" (is it a file that the user will need
        #  to provide?). Make sure to clarify for the user that some files
        #  written under inputs in the config file are actually intermediary
        #  output and that they don't need to be provided.
        # combine the historical data with the capacity expansion projections
        # then save to CSV to create the turbine data file (number_of_turbines)
        self.capacity_data.append(
            capacity_future,
            ignore_index=True,
            sort=True
        ).to_csv(
            self.turbine_data_filename,
            index=False
        )


        # get state column back by splitting p_name
        # ig1 and ig2 are dummy columns not used further
        _new_facility_id[
            ['region_id_2', 'ig1', 'ig2']
        ] = _new_facility_id.p_name.str.split('_',
                                              expand=True)

        # Calculate lat/long pairs for the future power plants
        _new_facility_locs = _new_facility_id[
            ['facility_id', 'region_id_2']
        ].merge(
            self.locs.groupby(
                by='region_id_2'
            ).mean().reset_index()[['region_id_2', 'lat', 'long']],
            on='region_id_2',
            how='left'
        )

        _new_facility_locs['facility_type'] = 'power plant'
        _new_facility_locs['region_id_1'] = 'USA'
        _new_facility_locs['region_id_3'] = ''
        _new_facility_locs['region_id_4'] = ''

        # Add the future power plants to the locations dataset stored in self
        # It has to go back into self to get saved at the end of the
        # join_facilities method
        self.locs = self.locs.append(
            _new_facility_locs,
            ignore_index=True,
            sort=True)

    def join_facilities(self, locations_output_file):
        """
        Join all facility data into single file
        """

        wind_plant_locations = ComputeLocations.wind_power_plant(self)
        landfill_locations_no_nulls = ComputeLocations.landfill(self)
        facility_locations = ComputeLocations.other_facility(self)

        locations = facility_locations.append(wind_plant_locations)
        locations = locations.append(landfill_locations_no_nulls)
        locations.reset_index(drop=True, inplace=True)

        # TODO: Isn't the code below duplicate? It seems that
        #  "ComputeLocations.wind_power_plant(self)" should already have
        #  removed GU, HI etc. If not duplicate could it be all handled
        #  once in the wind_power_plant method?
        # exclude Hawaii, Guam, Puerto Rico, and Alaska
        # (only have road network data for the contiguous United States)
        locations = locations[locations.region_id_2 != 'GU']
        locations = locations[locations.region_id_2 != 'HI']
        locations = locations[locations.region_id_2 != 'PR']
        locations = locations[locations.region_id_2 != 'AK']
        
        locations = locations[locations.region_id_3 != 'Nantucket']

        # find the entries in locations that have a duplicate facility_id AND
        # are not power plants.
        _ids_update = locations[locations.duplicated(subset='facility_id',
                                                     keep=False)]
        _ids_update = _ids_update.loc[_ids_update.facility_type != 'power plant'].index

        # Update the facility_id values for these entries in the locations data
        # frame.
        for i in _ids_update:
            locations.loc[i, 'facility_id'] = int(max(locations.facility_id) + 1)

        self.locs = locations

        self.capacity_projections()

        self.locs.to_csv(locations_output_file, index=False)
