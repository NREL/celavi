import pytest
from celavi.state_machine_units_model import Component
from celavi.state_machine_units_model import ComponentMaterial
from celavi.state_machine_units_model import Turbine
from celavi.state_machine_units_model import Inventory


class DummyContext:
    def __init__(self):
        self.landfill_material_inventory = Inventory()
        self.virgin_material_inventory = Inventory()


@pytest.fixture
def a_dummy_context_with_component_material():
    dummy_context = DummyContext()
    turbine = Turbine(turbine_id="test_turbine", latitude=39.9106, longitude=-105.2347)
    component = Component(
        context=dummy_context, component_type="Nacelle", parent_turbine=turbine
    )
    nacelle_aluminum = ComponentMaterial(
        parent_component=component,
        context=dummy_context,
        component_material="Nacelle Aluminum",
        material_type="Aluminum",
        material_tonnes=1,
        lifespan=50,
    )
    tower_steel = ComponentMaterial(
        parent_component=component,
        context=dummy_context,
        component_material="Tower Steel",
        material_type="Steel",
        material_tonnes=1,
        lifespan=75,
    )
    return dummy_context, nacelle_aluminum, tower_steel


def test_virgin_material(a_dummy_context_with_component_material):
    (
        dummy_context,
        nacelle_aluminum,
        tower_steel,
    ) = a_dummy_context_with_component_material
    nacelle_aluminum.transition("landfilling", 10)
    tower_steel.transition("landfilling", 50)
    assert (
        dummy_context.virgin_material_inventory.component_materials["Nacelle Aluminum"]
        == -1
    )
    assert (
        dummy_context.virgin_material_inventory.component_materials["Tower Steel"] == -1
    )


def test_landfill_material(a_dummy_context_with_component_material):
    (
        dummy_context,
        nacelle_aluminum,
        tower_steel,
    ) = a_dummy_context_with_component_material
    nacelle_aluminum.transition("landfilling", 10)
    tower_steel.transition("landfilling", 50)
    assert (
        dummy_context.landfill_material_inventory.component_materials[
            "Nacelle Aluminum"
        ]
        == 1
    )
    assert (
        dummy_context.landfill_material_inventory.component_materials["Tower Steel"]
        == 1
    )
