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
    print('File check OK.')


if __name__ == '__main__':
    main()
