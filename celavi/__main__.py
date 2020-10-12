from celavi.deprecated_state_machine_units_model import Context
from typing import List, Dict
import os
import matplotlib.pyplot as plt
import random
import datetime


def plot_landfill_and_virgin_material_inventories(
    context: Context, possible_component_materials: List[str]
) -> None:
    landfill_cumulative = context.landfill_material_inventory.cumulative_history
    virgin_cumulative = context.virgin_material_inventory.cumulative_history

    fig, axs = plt.subplots(
        ncols=3, nrows=len(possible_component_materials), figsize=(15, 10)
    )

    xs = range(len(landfill_cumulative))
    for cm, ax in zip(possible_component_materials, axs[:, 0]):
        ax.set_title(f"Landfill cumulative {cm}")
        ax.plot(xs, landfill_cumulative[cm])
        ax.set_ylabel("tonnes")
        ax.set_xlim(0, len(landfill_cumulative))

    xs = range(len(virgin_cumulative))
    for cm, ax in zip(possible_component_materials, axs[:, 1]):
        ax.set_title(f"Virgin cumulative {cm}")
        ax.plot(xs, virgin_cumulative[cm], color="r")
        ax.set_xlim(0, len(virgin_cumulative))

    xs = range(len(virgin_cumulative))
    for cm, ax in zip(possible_component_materials, axs[:, 2]):
        ax.set_title(f"Landfill/virgin {cm}")
        ax.plot(xs, landfill_cumulative[cm], color="b")
        ax.plot(xs, virgin_cumulative[cm], color="r")
        ax.set_xlim(0, len(virgin_cumulative))

    plt.tight_layout()
    plt.show()


def run_and_report():
    print(f">>> Start {datetime.datetime.now()}")

    possible_component_materials = [
        "Blade Glass Fiber",
        "Foundation High Strength Steel",
        "Nacelle Cast Iron",
        "Tower High Strength Steel",
        "Blade Carbon Fiber",
        "Nacelle Highly alloyed Steel",
        "Foundation Concrete",
        "Nacelle High Strength Steel",
    ]

    print(os.getcwd())

    context = Context(
        sd_model_filename="natl-wind-importable.py",
        component_material_state_log_filename="component_material_state_log.csv",
        year_intercept=1980.0,
        years_per_timestep=0.25,
        possible_component_materials=possible_component_materials,
    )
    context.populate_components("celavi_sample_10_turbines.csv")
    # context.populate_components("long_500_usgs_dataset_materials.csv")
    material_component_log, inventory_cumulative_logs = context.run()

    inventory_cumulative_logs.to_csv("inventory_cumulative_logs.csv", index=True)
    material_component_log.to_csv("material_component_log.csv", index=True)
    print(f"<<< End {datetime.datetime.now()}")

    plot_landfill_and_virgin_material_inventories(context, possible_component_materials)


if __name__ == "__main__":
    random.seed(0)
    run_and_report()
