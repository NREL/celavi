import pytest
from celavi.state_machine_units_model import Inventory


@pytest.fixture()
def an_inventory():
    timesteps = 100
    possible_component_materials = ["Tower Steel", "Nacelle Aluminum"]
    inventory = Inventory(possible_component_materials, timesteps)
    inventory.increment_material_quantity(component_material_name="Nacelle Aluminum", quantity=25, timestep=50)
    inventory.increment_material_quantity(component_material_name="Nacelle Aluminum", quantity=75, timestep=99)
    return inventory


def test_cumulative_material_inventory(an_inventory):
    expected = 100
    actual = an_inventory.component_materials["Nacelle Aluminum"]
    assert actual == expected
