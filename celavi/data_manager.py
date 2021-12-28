#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 08:05:13 2021

Uses code from Feedstock Production Emissions to Air Model (FPEAM) Copyright (c) 2018
Alliance for Sustainable Energy, LLC; Noah Fisher.
Builds on functionality in the FPEAM's Data.py.
Unmodified FPEAM code is available at https://github.com/NREL/fpeam.

@author: aeberle
"""

import pandas as pd


class Data(pd.DataFrame):
    """
    Data representation.
    """

    COLUMNS = []

    INDEX_COLUMNS = []

    def __init__(self, df=None, fpath=None, columns=None, backfill=True):

        _df = pd.DataFrame({}) if df is None and fpath is None else self.load(fpath=fpath,
                                                                              columns=columns)

        super(Data, self).__init__(data=_df)

        self.source = fpath or 'DataFrame'

        _valid = self.validate()

        try:
            assert _valid is True
        except AssertionError:
            if df is not None or fpath is not None:
                raise RuntimeError('{} failed validation'.format(__name__, ))
            else:
                pass

        if backfill:
            for _column in self.COLUMNS:
                if _column['backfill'] is not None:
                    self.backfill(column=_column['name'], value=_column['backfill'])

    def load(self, fpath, columns, memory_map=True, header=0, **kwargs):
        """
        Load data from a text file at <fpath>. Check and set column names.

        See pandas.read_table() help for additional arguments.

        :param fpath: [string] file path to budget file or SQLite database file
        :param columns: [dict] {name: type, ...}
        :param memory_map: [bool] load directly to memory for improved performance
        :param header: [int] 0-based row index containing column names
        :return: [DataFrame]
        """

        try:
            _df = pd.read_csv(filepath_or_buffer=fpath, sep=',', dtype=columns,
                              usecols=columns.keys(), memory_map=memory_map, header=header, **kwargs)
        except ValueError as e:
            if e.__str__() == 'Usecols do not match names.':
                from collections import Counter
                _df = pd.read_table(filepath_or_buffer=fpath, sep=',', dtype=columns,
                                    memory_map=memory_map, header=header, **kwargs)
                _df_columns = Counter(_df.columns)
                _cols = list(set(columns.keys()) - set(_df_columns))
                raise ValueError('%(f)s missing columns: %(cols)s' % (dict(f=fpath, cols=_cols)))
            else:
                raise e
        else:
            return _df

    def backfill(self, column, value=0):
        """
        Replace NaNs in <column> with <value>.

        :param column: [string]
        :param value: [any]
        :return:
        """

        _dataset = str(type(self)).split("'")[1]

        _backfilled = False

        # if any values are missing,
        if self[column].isna().any():
            # count the missing values
            _count_missing = sum(self[column].isna())
            # count the total values
            _count_total = self[column].__len__()

            # fill the missing values with zeros
            self[column].fillna(value, inplace=True)

            # log a warning with the number of missing values
            print('%s of %s data values in %s.%s were backfilled as %s' % (_count_missing, _count_total, _dataset, column, value))

            _backfilled = True

        else:
            # log if no values are missing
            print('no missing data values in %s.%s' % (_dataset, column))

        return _backfilled

    def validate(self):
        """
        Check that data are not empty

        :return:
        """
        _name = type(self).__name__

        _valid = True

        print('validating %s' % (_name, ))

        if self.empty:
            print('no data provided for %s' % (_name, ))
            _valid = False

        print('validated %s' % (_name, ))

        return _valid

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # process exceptions
        if exc_type is not None:
            print('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self


class TransportationGraph(Data):

    COLUMNS = ({'name': 'edge_id', 'type': int, 'index': True, 'backfill': None},
               {'name': 'statefp', 'type': str, 'index': False, 'backfill': None},
               {'name': 'countyfp', 'type': str, 'index': False, 'backfill': None},
               {'name': 'u_of_edge', 'type': int, 'index': False, 'backfill': None},
               {'name': 'v_of_edge', 'type': int, 'index': False, 'backfill': None},
               {'name': 'weight', 'type': float, 'index': False, 'backfill': None},
               {'name': 'fclass', 'type': int, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(TransportationGraph, self).__init__(df=df, fpath=fpath, columns=columns,
                                                  backfill=backfill)


class TransportationNodeLocations(Data):

    COLUMNS = ({'name': 'node_id', 'type': int, 'index': True, 'backfill': None},
               {'name': 'long', 'type': float, 'index': False, 'backfill': None},
               {'name': 'lat', 'type': float, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(TransportationNodeLocations, self).__init__(df=df, fpath=fpath, columns=columns,
                                                          backfill=backfill)


class Locations(Data):
    COLUMNS = ({'name': 'facility_id', 'type': int, 'index': True, 'backfill': None},
               {'name': 'facility_type', 'type': str, 'index': False, 'backfill': None},
               {'name': 'long', 'type': float, 'index': False, 'backfill': None},
               {'name': 'lat', 'type': float, 'index': False, 'backfill': None},
               {'name': 'region_id_1', 'type': str, 'index': False, 'backfill': None},
               {'name': 'region_id_2', 'type': str, 'index': False, 'backfill': None},
               {'name': 'region_id_3', 'type': str, 'index': False, 'backfill': None},
               {'name': 'region_id_4', 'type': str, 'index': False, 'backfill': None}
               )

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(Locations, self).__init__(df=df, fpath=fpath, columns=columns,
                                                          backfill=backfill)


class TurbineLocations(Data):
    COLUMNS = ({'name': 'eia_id', 'type': float, 'index': True, 'backfill': '-1'},
               {'name': 't_state', 'type': str, 'index': False, 'backfill': None},
               {'name': 't_county', 'type': str, 'index': False, 'backfill': None},
               {'name': 'p_name', 'type': str, 'index': False, 'backfill': None},
               {'name': 'p_year', 'type': float, 'index': False, 'backfill': '-1'},
               {'name': 'p_tnum', 'type': float, 'index': False, 'backfill': '-1'},
               {'name': 't_model', 'type': str, 'index': False, 'backfill': None},
               {'name': 't_fips', 'type': int, 'index': False, 'backfill': None},
               {'name': 'xlong', 'type': float, 'index': False, 'backfill': None},
               {'name': 'ylat', 'type': float, 'index': False, 'backfill': None},
               {'name': 'p_cap', 'type': float, 'index': False, 'backfill': None},
               {'name': 't_cap', 'type': float, 'index': False, 'backfill': None}
               )

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(TurbineLocations, self).__init__(df=df, fpath=fpath, columns=columns,
                                                          backfill=backfill)

class OtherFacilityLocations(Data):
    COLUMNS = ({'name': 'facility_id', 'type': int, 'index': True, 'backfill': None},
               {'name': 'facility_type', 'type': str, 'index': False, 'backfill': None},
               {'name': 'lat', 'type': float, 'index': False, 'backfill': None},
               {'name': 'long', 'type': float, 'index': False, 'backfill': None},
               {'name': 'region_id_1', 'type': str, 'index': False, 'backfill': None},
               {'name': 'region_id_2', 'type': str, 'index': False, 'backfill': None},
               {'name': 'region_id_3', 'type': str, 'index': False, 'backfill': None},
               {'name': 'region_id_4', 'type': str, 'index': False, 'backfill': None}
               )

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(OtherFacilityLocations, self).__init__(df=df, fpath=fpath, columns=columns,
                                               backfill=backfill)

class LandfillLocations(Data):
    COLUMNS = ({'name': 'Landfill ID', 'type': int, 'index': True, 'backfill': None},
               {'name': 'State', 'type': str, 'index': False, 'backfill': None},
               {'name': 'Latitude', 'type': float, 'index': False, 'backfill': None},
               {'name': 'Longitude', 'type': float, 'index': False, 'backfill': None},
               {'name': 'City', 'type': str, 'index': False, 'backfill': None},
               {'name': 'County', 'type': str, 'index': False, 'backfill': None},
               {'name': 'Current Landfill Status', 'type': str, 'index': False, 'backfill': None},
               {'name': 'Landfill Closure Year', 'type': str, 'index': False, 'backfill': '-1'},
               )

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(LandfillLocations, self).__init__(df=df, fpath=fpath, columns=columns,
                                               backfill=backfill)

class StandardScenarios(Data):
    COLUMNS = ({'name': 'state', 'type': str, 'index': True, 'backfill': None},
               {'name': 't', 'type': int, 'index': False, 'backfill': None},
               {'name': 'wind-ons_MW', 'type': float, 'index': False, 'backfill': '-1'}
               )

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(StandardScenarios,self).__init__(df=df, fpath=fpath, columns=columns,
                                               backfill=backfill)


class RoutePairs(Data):
    COLUMNS = ({'name': 'source_facility_type', 'type': str, 'index': True, 'backfill': None},
               {'name': 'destination_facility_type', 'type': str, 'index': True,'backfill': None},
               {'name': 'in_state_only', 'type': bool, 'index': False, 'backfill': None},
               {'name': 'vkmt_max', 'type': float, 'index': False, 'backfill': 1.0e9}
               )

    def __init__(self, df=None, fpath=None,
                 columns={d['name']: d['type'] for d in COLUMNS for k in d.keys()},
                 backfill=True):
        super(RoutePairs,self).__init__(df=df, fpath=fpath, columns=columns,
                                        backfill=backfill)
