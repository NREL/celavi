from dataclasses import dataclass, field
from typing import List, Dict
from uuid import uuid4
import pandas as pd


def unique_identifer_str():
    """
    This returns a UUID that can serve as a unique identifier for anything.
    These UUIDs can be used as keys in a set or hash if needed.

    Returns
    -------
    str
        A UUID to be used as a unique identifier.
    """
    return str(uuid4())


@dataclass
class Material:
    name: str
    tonnes: float


@dataclass
class Component:
    name: str
    materials: Dict[str, Material]
    id: field(default_factory=unique_identifer_str)


class Turbine:
    def __init__(self,
                 model: pd.DataFrame,
                 hub_height_m: float,
                 capacity_mw: float,
                 rotor_diameter_m: float):
        for _, row in model.iterrows():
            component = row["Component"]
            material = row["Material"]
            intercept = row["Intercept"]
            rd_tonne_per_m = row["Blade.diam.m.coeff"]
            hh_tonne_per_m = row["Hub.height.m.coeff"]
            capacity_tonne_per_mw = row["Capacity.MW.coeff"]
            value = intercept + \
                    (rotor_diameter_m * rd_tonne_per_m) + \
                    (hub_height_m * hh_tonne_per_m) + \
                    (capacity_mw * capacity_tonne_per_mw)
            print(component, material, value)


if __name__ == "__main__":
    turbine_model = pd.read_csv("component_material_linear_models.csv")
    turb = Turbine(turbine_model, hub_height_m=78, capacity_mw=2, rotor_diameter_m=80)

