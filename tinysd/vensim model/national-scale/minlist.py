"""
Python model "minlist.py"
Translated using PySD version 0.10.0
"""
from __future__ import division
import numpy as np
from pysd import utils
import xarray as xr

from pysd.py_backend.functions import cache
from pysd.py_backend import functions

_subscript_dict = {}

_namespace = {
    'TIME': 'time',
    'Time': 'time',
    'input1': 'input1',
    'input2': 'input2',
    'input3': 'input3',
    'input4': 'input4',
    'MINLIST': 'minlist'
}

__pysd_version__ = "0.10.0"

__data = {'scope': None, 'time': lambda: 0}


def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


def time():
    return __data['time']()


@cache('step')
def minlist():
    """
    Real Name: b'MINLIST'
    Original Eqn: b'MIN(input1, MIN(input2, MIN(input3, input4)))'
    Units: b'input1'
    Limits: (None, None)
    Type: component

    b''
    """
    return np.minimum(input1(), np.minimum(input2(), np.minimum(input3(), input4())))
