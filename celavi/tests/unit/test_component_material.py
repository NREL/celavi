import pytest
from celavi.state_machine_units_model import Component
from celavi.state_machine_units_model import ComponentMaterial
from celavi.state_machine_units_model import Turbine


@pytest.fixture
def a_component_material():
    turbine = Turbine(turbine_id="test_turbine", latitude=39.9106, longitude=-105.2347)
    component = Component(context=None, component_type="Nacelle", parent_turbine=turbine)
    component_material = ComponentMaterial(parent_component=component, context=None, component_material="Nacelle Aluminum", material_type="Aluminum", material_tonnes=1, lifespan=50)
    return component_material


def test_material_type(a_component_material):
    assert a_component_material.material_type == "Aluminum"
