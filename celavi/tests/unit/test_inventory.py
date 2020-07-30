import pytest
from celavi.state_machine_units_model import Inventory

@pytest.fixture()
def an_inventory():
    inventory = Inventory("tonne")
    inventory.increment_material_quantity(material="Al", quantity=100)
    return inventory


def test_material_present(an_inventory):
    assert an_inventory.check_if_material_present("Al", 100)
