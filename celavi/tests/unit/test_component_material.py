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


def test_use_landfill(a_component_material):
    a_component_material.state = "use"
    a_component_material.transition("landfilling")
    assert a_component_material.state == "landfill"


def test_use_reuse(a_component_material):
    a_component_material.state = "use"
    a_component_material.transition("reusing")
    assert a_component_material.state == "reuse"


def test_use_recycle(a_component_material):
    a_component_material.state = "use"
    a_component_material.transition("recycling")
    assert a_component_material.state == "recycle"


def test_use_remanufacture(a_component_material):
    a_component_material.state = "use"
    a_component_material.transition("remanufacturing")
    assert a_component_material.state == "remanufacture"


def test_use_recycle(a_component_material):
    a_component_material.state = "use"
    a_component_material.transition("recycling")
    assert a_component_material.state == "recycle"


def test_reuse_landfill(a_component_material):
    a_component_material.state = "reuse"
    a_component_material.transition("landfilling")
    assert a_component_material.state == "landfill"


def test_recycle_manufacture(a_component_material):
    a_component_material.state = "recycle"
    a_component_material.transition("manufacturing")
    assert a_component_material.state == "manufacture"


def test_remanufacture_use(a_component_material):
    a_component_material.state = "remanufacture"
    a_component_material.transition("using")
    assert a_component_material.state == "use"


def test_manufacture_use(a_component_material):
    a_component_material.state = "manufacture"
    a_component_material.transition("using")
    assert a_component_material.state == "use"
