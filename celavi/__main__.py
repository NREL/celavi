from celavi.state_machine_units_model import Context
from typing import List, Dict
import pandas as pd
import os
import matplotlib.pyplot as plt
import random
import numpy as np


def plot_landfill_and_virgin_material_inventories(context: Context, possible_component_materials: List[str]) -> None:
    landfill_cumulative = context.landfill_material_inventory.cumulative_history
    timesteps = np.arange(len(landfill_cumulative))
    landfill_cumulative["timestep"] = timesteps
    landfill_melt = pd.melt(landfill_cumulative, id_vars=["timestep"], value_vars=possible_component_materials)
    fig, axs = plt.subplots(ncols=1, nrows=len(possible_component_materials), figsize=(10, 10))
    for cm, ax in zip(possible_component_materials, axs):
        ax.set_title(cm)
    plt.tight_layout()
    plt.show()

def run_and_report():
    possible_component_materials = [
        "Blade Glass Fiber",
        "Foundation High Strength Steel",
        "Nacelle Cast Iron",
        "Tower High Strength Steel",
        "Blade Carbon Fiber",
        "Nacelle Highly alloyed Steel",
        "Foundation Concrete",
        "Nacelle High Strength Steel"
    ]

    print(os.getcwd())

    context = Context(
        "natl-wind-importable.py", year_intercept=1980.0, years_per_timestep=0.25,
        possible_component_materials=possible_component_materials
    )
    context.populate_components("celavi_sample_10_turbines.csv")
    material_component_log = context.run()

    plot_landfill_and_virgin_material_inventories(context, possible_component_materials)


if __name__ == "__main__":
    random.seed(0)
    run_and_report()
