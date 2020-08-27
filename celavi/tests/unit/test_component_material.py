import pytest
from celavi.state_machine_units_model import Component
from celavi.state_machine_units_model import ComponentMaterial
from celavi.state_machine_units_model import Turbine
from celavi.state_machine_units_model import Inventory


class DummyContext:
    def __init__(self):
        timesteps = 10
        possible_component_materials = ["Tower Steel", "Nacelle Aluminum"]
        self.landfill_material_inventory = Inventory(
            possible_component_materials, timesteps
        )
        self.virgin_material_inventory = Inventory(
            possible_component_materials, timesteps
        )
        self.remanufacture_material_inventory = Inventory(
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
        )
        self.use_material_inventory = Inventory(
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
        )
        self.remanufacture_material_inventory = Inventory(
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
        )
        self.reuse_material_inventory = Inventory(
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
        )
        self.recycle_material_inventory = Inventory(
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
        )


@pytest.fixture
def a_component_material():
    turbine = Turbine(turbine_id="test_turbine", latitude=39.9106, longitude=-105.2347)
    component = Component(
        context=DummyContext(), component_type="Nacelle", parent_turbine=turbine
    )
    component_material = ComponentMaterial(
        parent_component=component,
        context=DummyContext(),
        name="Nacelle Aluminum",
        material_type="Aluminum",
        material_tonnes=1,
        lifespan=50,
    )
    return component_material


def test_material_type(a_component_material):
    assert a_component_material.material_type == "Aluminum"


def test_use_landfill(a_component_material):
    a_component_material.state = "use"
    a_component_material.transition("landfilling", 1)
    assert a_component_material.state == "manufacture"


def test_use_reuse(a_component_material):
    a_component_material.state = "use"
    a_component_material.transition("reusing", 1)
    assert a_component_material.state == "reuse"


def test_use_recycle(a_component_material):
    a_component_material.state = "use"
    a_component_material.transition("recycling", 1)
    assert a_component_material.state == "recycle"


def test_use_remanufacture(a_component_material):
    a_component_material.state = "use"
    a_component_material.transition("remanufacturing", 1)
    assert a_component_material.state == "remanufacture"


def test_reuse_landfill(a_component_material):
    a_component_material.state = "reuse"
    a_component_material.transition("landfilling", 1)
    assert a_component_material.state == "manufacture"


def test_recycle_manufacture(a_component_material):
    a_component_material.state = "recycle"
    a_component_material.transition("manufacturing", 1)
    assert a_component_material.state == "manufacture"


def test_remanufacture_use(a_component_material):
    a_component_material.state = "remanufacture"
    a_component_material.transition("using", 1)
    assert a_component_material.state == "use"


def test_manufacture_use(a_component_material):
    a_component_material.state = "manufacture"
    a_component_material.transition("using", 1)
    assert a_component_material.state == "use"


def test_landfill_to_manufacture(a_component_material):
    a_component_material.state = "landfill"
    a_component_material.transition("manufacturing", 1)
    assert a_component_material.state == "manufacture"
