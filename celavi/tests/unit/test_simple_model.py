import pytest
import pandas as pd

from celavi.simple_model import Context


@pytest.fixture
def components():
    turbine = [
        {
            "type": "blade",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "type": "blade",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "type": "blade",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "type": "nacelle",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "type": "tower",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "type": "foundation",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
    ]
    return pd.DataFrame(turbine)


@pytest.fixture
def context():
    return Context()


def test_years_to_timestep(context):
    expected = 160
    actual = context.years_to_timesteps(2020)
    assert expected == actual


def test_population(context, components):
    context.populate(components)
    expected = 6
    actual = len(context.components)
    assert expected == actual
