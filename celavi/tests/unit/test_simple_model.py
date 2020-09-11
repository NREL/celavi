import pytest
import pandas as pd

from celavi.simple_model import Context


@pytest.fixture
def components():
    turbine = [
        {
            "kind": "blade",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "kind": "blade",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "kind": "blade",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "kind": "nacelle",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "kind": "tower",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2020,
        },
        {
            "kind": "foundation",
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


def test_context_run(context, components):
    context.populate(components)
    context.run()
