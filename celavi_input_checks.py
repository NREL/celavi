import pandas as pd
import numpy as np
import os.path
import argparse


class FileChecks:
    """
    FileChecks has a bunch of methods to check the integrity of files
    used as input to CELAVI. See the docstrings for each individual
    method for explanations.

    The basic idea is that each of the methods are called and each method
    performs input checks.  If all the input cheks pass, these methods
    run to completion and returns nothing. However, if there are errors
    found, each respective method will raise and exception describing the
    error. These exceptions shouldn't be caught; rather, they should term-
    inate the program so that the exception is shown. The exceptions are
    created with descriptive messages before they are raised.
    """

    def __init__(self, locations, step_costs, fac_edges, routes, transpo_edges):
        """
        Initializes the file integrity checks by coopying the filenames
        to instance variables.

        Parameters
        ----------
        locations: str
            Path to the locations file

        step_costs: str
            Path to the step_costs file

        fac_edges: str
            Path to the facility edges file

        routes: str
            Path to the routes file

        transpo_edges: str
            Path to the transportation edges file
        """
        self.locations_filename = locations
        self.step_costs_filename = step_costs
        self.fac_edges_filename = fac_edges
        self.routes_filename = routes
        self.transpo_edges_filename = transpo_edges

        self.locations: pd.DataFrame = None
        self.step_costs: pd.DataFrame = None
        self.fac_edges: pd.DataFrame = None
        self.routes: pd.DataFrame = None
        self.transpo: pd.DataFrame = None

    def check_files_exist(self) -> bool:
        """
        This method checks to see if files exist before trying
        to open them.

        Returns
        -------
        bool
            True if all the files exist

        Raises
        ------
        Exception
            Raises an exception if one of the files does not exist
        """
        if not os.path.isfile(self.locations_filename):
            raise Exception(f'Locations file {self.locations_filename} is not a file.')

        if not os.path.isfile(self.step_costs_filename):
            raise Exception(f'Step costs file {self.step_costs_filename} is not a file.')

        if not os.path.isfile(self.fac_edges_filename):
            raise Exception(f'Facility edges file {self.fac_edges_filename} is not a file.')

        if not os.path.isfile(self.routes_filename):
            raise Exception(f'Routes file {self.routes_filename} is not a file.')

        if not os.path.isfile(self.transpo_edges_filename):
            raise Exception(f'Transportation edges file {self.transpo_edges_filename} is not a file.')

        return True

    def open_files(self) -> None:
        """
        This method attempts to open each file as a .csv and load it
        into pandas.

        Raises
        ------
        Exception
            Raises an exception if any of the files fail to open as .csv
            files.
        """
        try:
            self.locations = pd.read_csv(self.locations_filename)
        except (pd.EmptyDataError, FileNotFoundError):
            raise Exception(f'{self.locations_filename} failed to read as a .csv')

        try:
            self.step_costs = pd.read_csv(self.step_costs_filename)
        except (pd.EmptyDataError, FileNotFoundError):
            raise Exception(f'{self.step_costs_filename} failed to read as a .csv')

        try:
            self.fac_edges = pd.read_csv(self.fac_edges_filename)
        except (pd.EmptyDataError, FileNotFoundError):
            raise Exception(f'{self.fac_edges_filename} failed to read as a .csv')

        try:
            self.routes = pd.read_csv(self.routes_filename)
        except (pd.EmptyDataError, FileNotFoundError):
            raise Exception(f'{self.routes_filename} failed to read as a .csv')

        try:
            self.transpo_edges = pd.read_csv(self.transpo_edges_filename)
        except (pd.EmptyDataError, FileNotFoundError):
            raise Exception(f'{self.transpo_edges_filename} failed to read as a .csv')

    def check_facility_id_nulls(self):
        """
        This method checks the facility_id columns across the tables

        Raises
        ------
        Exception
            Raises an exception if any null values are found.
        """
        if self.locations['facility_id'].isnull().values.any():
            raise Exception(f'facility_id in locations has an empty value.')

        if self.step_costs['facility_id'].isnull().values.any():
            raise Exception(f'destination_facility_id in step costs has an empty value.')

        if self.routes['source_facility_id'].isnull().values.any():
            raise Exception(f'source_facility_id in routes has an empty value.')

        if self.routes['destination_facility_id'].isnull().values.any():
            raise Exception(f'destination_facility_id in routes has an empty value.')

    def check_facility_type_nulls(self):
        """
        This tests for any null values in facility_type columns

        Raises
        ------
        Exception
            Raises an exception if any values are null
        """
        if self.locations['facility_type'].isnull().values.any():
            raise Exception('facility_type in locations has an empty value.')

        if self.fac_edges['facility_type'].isnull().values.any():
            raise Exception('facility_type in fac_edges has an empty value.')

        if self.routes['source_facility_type'].isnull().values.any():
            raise Exception('source_facility_type in routes has an empty value.')

        if self.routes['destination_facility_type'].isnull().values.any():
            raise Exception('destination_facility_type in routes has an empty value.')

    def check_lat_long_nulls(self):
        """
        The tests for any null latitude values

        Raises
        ------
        Exception
            Raises an exception if any values are found to be missing
        """
        if self.locations['lat'].isnull().values.any():
            raise Exception('lat in locations has an empty value.')

        if self.locations['long'].isnull().values.any():
            raise Exception('long in locations has an empty value.')

    def check_step_nulls(self):
        """
        Checks to see if there are any nulls in the u_step or v_step
        columns. Also check transpo_cost_method

        Raises
        ------
        Exception
            Raises an exception if the u_step, v_step, step, or
            step_cost_method are empty.
        """
        if self.transpo_edges['u_step'].isnull().values.any():
            raise Exception('u_step in transpo_edges has a null value.')

        if self.transpo_edges['v_step'].isnull().values.any():
            raise Exception('v_step in transpo_edges has a null value.')

        if self.step_costs['step_cost_method'].isnull().values.any():
            raise Exception('step_cost_method in step_costs has a null value')

        if self.transpo_edges['transpo_cost_method'].isnull().values.any():
            raise Exception('transpo_cost_method in transpo_edges has a null value')

        if self.fac_edges['step'].isnull().values.any():
            raise Exception('step in fac_edges has a null value')

    def check_joins_on_facility_id(self):
        """
        Checks the joins on facility_id among the tables.

        Raises
        ------
        Exception
            Raises an exception if the joins do not work.
        """

        # Check both sides of the join
        join1 = self.locations.merge(self.step_costs, on='facility_id', how='outer')
        if join1['facility_type'].isna().values.any():
            step_cost_facility_id = join1[join1['facility_type'].isna()]['facility_id'].values
            raise Exception(f'There is a step_costs facility_id of {step_cost_facility_id} that does not exist in locations.facility_id')
        if join1['step'].isna().values.any():
            location_facility_id = join1[join1['step'].isna()]['facility_id'].values
            raise Exception(f'There is a locations.facility_id of {location_facility_id} that does not exit in step_costs.facility_id')

        # Check left side of join only (routes doesn't use all locations)
        join2 = self.locations.merge(self.routes, left_on='facility_id', right_on='source_facility_id', how='outer')
        if join2['facility_id'].isna().values.any():
            location_facility_id = join2[join2['facility_id'].isna().values]['source_facility_id'].values
            raise Exception(f'There is a routes.source_facility_id of {location_facility_id} that does not exist in locations.facility_id')

        # Check left side of join only (routes doesn't use all locations)
        join3 = self.locations.merge(self.routes, left_on='facility_id', right_on='destination_facility_id', how='outer')
        if join3['facility_id'].isna().values.any():
            destination_facility_id = join3[join3['facility_id'].isna().values]['destination_facility_id'].values
            raise Exception(
                f'There is a routes.destination_facility_id of {destination_facility_id} that does not exist in locations.facility_id')

        # Check left side of join only (routes doesn't use all step_cost locations)
        join4 = self.step_costs.merge(self.routes, left_on='facility_id', right_on='source_facility_id', how='outer')
        if join4['facility_id'].isna().values.any():
            source_facility_id = join4[join4['facility_id'].isna().values]['source_facility_id']
            raise Exception(f'There is a routes.source_facility_id {source_facility_id} that is not in step_costs.facility_id')

        # Check left side of join only (routes doesn't use all step_cost locations)
        join5 = self.step_costs.merge(self.routes, left_on='facility_id', right_on='destination_facility_id',
                                      how='outer')
        if join5['facility_id'].isna().values.any():
            destination_facility_id = join5[join5['facility_id'].isna().values]['source_facility_id']
            raise Exception(
                f'There is a routes.destination_facility_id {destination_facility_id} that is not in step_costs.facility_id')

    def check_joins_on_facility_type(self):
        """
        Check the joins on the facility_type among the tables

        Raises
        ------
        Exception
            Raises an exception if there are any problems with the
            facility_types.
        """

        # Check both sides of join
        join1 = self.locations.merge(self.fac_edges, on='facility_type', how='outer')
        if join1['facility_id'].isna().values.any():
            facility_type = join1[join1['facility_id'].isna().values]['facility_type'].values
            raise Exception(
                f'There is a fac_edges.facility_type {facility_type} that does not exist in locations.facility_type')
        if join1['step'].isna().values.any():
            facility_type = join1[join1['step'].isna().values]['facility_type'].values
            raise Exception(
                f'There is a locations.facility_type {facility_type} that does not exist in fac_edges.facility_type')

        # Check left side of join only (not all facility types are used in routes)
        join2 = self.locations.merge(self.routes, left_on='facility_type', right_on='source_facility_type', how='outer')
        if join2['facility_type'].isna().values.any():
            source_facility_type = join2[join2['facility_type'].isna().values]['source_facility_type'].values
            raise Exception(
                f'There is a routes.source_facility_type {source_facility_type} that does not exist in locations.facility_type.'
            )

        # Check left side of join only (not all facility types are used in routes)
        join3 = self.fac_edges.merge(self.routes, left_on='facility_type', right_on='source_facility_type', how='outer')
        if join3['facility_type'].isna().values.any():
            source_facility_type = join3[join3['facility_type'].isna().values]['source_facility_type'].values
            raise Exception(
                f'There is a routes.source_facility_type {source_facility_type} that does not exist in fac_edges.facility_type'
            )

        # Check left side of join only (not all facility types are used in routes)
        join4 = self.locations.merge(self.routes, left_on='facility_type', right_on='destination_facility_type', how='outer')
        if join4['facility_type'].isna().values.any():
            destination_facility_type = join4[join4['facility_type'].isna().values]['destination_facility_type'].values
            raise Exception(
                f'There is a routes.destination_facility_type {destination_facility_type} that does not exist in locations.facility_type.'
            )

    def check_step_joins(self):
        """
        Checks all joins that involve steps.

        Raises
        ------
        Exception
            Raises an exception if there are any problems with the step ids.
        """

        # Check both sides of join
        join1 = self.step_costs.merge(self.fac_edges, on='step', how='outer')
        if join1['facility_type'].isna().values.any():
            step = join1[join1['facility_type'].isna().values]['step'].values
            raise Exception(f'There is a step_costs.step of {step} that does not exist in fac_edges.step.')
        if join1['step_cost_method'].isna().values.any():
            step = join1[join1['step_cost_method'].isna().values]['step'].values
            raise Exception(f'There is a fac_edges.step {step} that does not exist in step_cost_method.step.')

        # Check left side of join only
        join2 = self.step_costs.merge(self.transpo_edges, left_on='step', right_on='u_step', how='outer')
        if join2['step'].isna().values.any():
            u_step = join2[join2['step'].isna().values]['u_step'].values
            raise Exception(f'There is a transpo_edges.u_step {u_step} that does not exist in step_costs.step.')

        # Check left side of join only
        join3 = self.step_costs.merge(self.transpo_edges, left_on='step', right_on='v_step', how='outer')
        if join3['step'].isna().values.any():
            v_step = join3[join3['step'].isna().values]['v_step'].values
            raise Exception(f'There is a transpo_edges.v_step {v_step} that does not exist in step_costs.step.')

        # Check left side of join only
        join4 = self.step_costs.merge(self.fac_edges, left_on='step', right_on='next_step', how='outer')
        if join4['step_x'].isna().values.any():
            next_step = join4[join4['step_x'].isna().values]['next_step'].values
            next_step_not_all_na = join4[join4['step_x'].isna().values]['next_step'].isna().values.all()
            if not next_step_not_all_na:   # next_step is optional, so nan should not throw an error
                raise Exception(f'There is a fac_edges.next_step {next_step} that does not exist in step_costs.step.')


def main():
    # Filenames
    # locations, step_costs, fac_edges, routes, transpo_edges
    parser = argparse.ArgumentParser(description='Check CELAVI input data')
    parser.add_argument('--locations', help='Path to locations file')
    parser.add_argument('--step_costs', help='Path to step_costs file')
    parser.add_argument('--fac_edges', help='Facility edges file')
    parser.add_argument('--routes', help='Routes file')
    parser.add_argument('--transpo_edges', help='Transportation edges file')
    args = parser.parse_args()
    file_checks = FileChecks(
        locations=args.locations,
        step_costs=args.step_costs,
        fac_edges=args.fac_edges,
        routes=args.routes,
        transpo_edges=args.transpo_edges
    )
    file_checks.check_files_exist()
    file_checks.open_files()
    file_checks.check_facility_id_nulls()
    file_checks.check_facility_type_nulls()
    file_checks.check_step_nulls()
    file_checks.check_joins_on_facility_id()
    file_checks.check_joins_on_facility_type()
    file_checks.check_step_joins()
    print('File check OK.')


if __name__ == '__main__':
    main()
