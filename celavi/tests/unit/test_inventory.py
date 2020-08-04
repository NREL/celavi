import pytest
from celavi.state_machine_units_model import Inventory

@pytest.fixture()
def an_inventory():
    inventory = Inventory("tonne")
    inventory.increment_material_quantity(material="Al", quantity=25, timestep=50)
    inventory.increment_material_quantity(material="Al", quantity=75, timestep=100)
    return inventory


def test_material_present(an_inventory):
    assert an_inventory.check_material("Al", 100)


def test_material_history_timestamps(an_inventory):
    expected_timestamps = [50, 100]
    actual_timestamps = an_inventory.materials_history.keys()
    for x, y in zip(expected_timestamps, actual_timestamps):
        assert x == y


def test_material_quantities(an_inventory):
    expected_aluminum_quantities = [25, 100]
    actual_aluminum_quantities = []
    for materials in an_inventory.materials_history.values():
        actual_aluminum_quantities.append(materials["Al"])
    for x, y in zip(expected_aluminum_quantities, actual_aluminum_quantities):
        assert x == y
