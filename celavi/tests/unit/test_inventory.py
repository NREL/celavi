import numpy as np
import pandas as pd
import pytest
from celavi.state_machine_units_model import Inventory


@pytest.fixture()
def an_inventory():
    timesteps = 10
    possible_component_materials = ["Tower Steel", "Nacelle Aluminum"]
    inventory = Inventory(possible_component_materials, timesteps)
    inventory.increment_material_quantity(
        component_material_name="Nacelle Aluminum", quantity=25, timestep=5
    )
    inventory.increment_material_quantity(
        component_material_name="Nacelle Aluminum", quantity=25, timestep=7
    )
    inventory.increment_material_quantity(
        component_material_name="Tower Steel", quantity=75, timestep=9
    )
    return inventory


def test_cumulative_material_inventory(an_inventory):
    expected = 50
    actual = an_inventory.component_materials["Nacelle Aluminum"]
    assert actual == expected


def test_material_inventory_history_nacelle_aluminum(an_inventory):
    expected = 25
    actual = an_inventory.component_materials_history[5]["Nacelle Aluminum"]
    assert actual == expected


def test_material_inventory_history_tower_steel(an_inventory):
    expected = 0
    actual = an_inventory.component_materials_history[5]["Tower Steel"]
    assert actual == expected


def test_material_inventory_cumulative_history(an_inventory):
    expected = pd.DataFrame({"Tower Steel": np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 75.0]),
                             "Nacelle Aluminum": np.array([0.0, 0.0, 0.0, 0.0, 0.0, 25.0, 25.0, 50.0, 50.0, 50.0])})
    actual = an_inventory.cumulative_history
    assert actual.equals(expected)
