import pytest

from celavi.simple_model import Context


@pytest.fixture
def context():
    return Context()


def test_years_to_timestep(context):
    expected = 160
    actual = context.years_to_timesteps(2020)
    assert expected == actual
