import pandas as pd
import os.path
import argparse


class FileChecks:
    """
    FileChecks has a bunch of methods to check the integrity of files
    used as input to CELAVI. See the docstrings for each individual
    method for explanations.
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

        if self.routes['source_lat'].isnull().values.any():
            raise Exception('source_lat in routes has an empty value.')

        if self.routes['source_long'].isnull().values.any():
            raise Exception('source_long in routes has an empty value.')

        if self.routes['destination_lat'].isnull().values.any():
            raise Exception('destination_lat in routes has an empty value.')

        if self.routes['destination_long'].isnull().values.any():
            raise Exception('destination_long in routes has an empty value.')


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
    print('File check OK.')


if __name__ == '__main__':
    main()
