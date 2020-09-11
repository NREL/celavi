import pytest
import pandas as pd
from random import randint, seed

from celavi.simple_model import Context


lifespan_fns = {
    "nacelle": lambda: randint(30, 40),
    "blade": lambda: 20,
    "foundation": lambda: randint(50, 100),
    "tower": lambda: 50,
}


@pytest.fixture
def components():
    turbine = [
        {
            "kind": "blade",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2000,
        },
        {
            "kind": "blade",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2000,
        },
        {
            "kind": "blade",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2000,
        },
        {
            "kind": "nacelle",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2000,
        },
        {
            "kind": "tower",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2000,
        },
        {
            "kind": "foundation",
            "xlat": 39.9106,
            "ylon": -105.2347,
            "year": 2000,
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


def test_timesteps_to_years(context):
    expected = 2000
    actual = context.timesteps_to_years(80)
    assert expected == actual


def test_population(context, components):
    seed(0)
    context.populate(components, lifespan_fns)
    expected = 6
    actual = len(context.components)
    assert expected == actual


def test_context_run(context, components):
    seed(0)
    context.populate(components, lifespan_fns)
    context.run()
