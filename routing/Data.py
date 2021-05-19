import pandas as pd
from IO import load


class Data(pd.DataFrame):
    """
    FPEAM data representation.
    """

    COLUMNS = []

    INDEX_COLUMNS = []

    def __init__(self, df=None, fpath=None, columns=None, backfill=True):

        _df = pd.DataFrame({}) if df is None and fpath is None else load(fpath=fpath,
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

    def summarize(self):
        # @TODO: add summarization methods
        raise NotImplementedError

    def validate(self):

        # @TODO: add validation methods
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
