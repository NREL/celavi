from tinylca.state_machine_units_model import Context
from typing import List, Dict
import pandas as pd
import os
import matplotlib.pyplot as plt
import random
import numpy as np


def report(result):
    max_timestep = int(result["ts"].max())
    report_list: List[Dict] = []
    for ts in range(1, max_timestep + 1):
        timestep_result = result[result["ts"] == ts]
        number_use = len(timestep_result[timestep_result["component.state"] == "use"])
        number_recycle = len(
            timestep_result[timestep_result["component.state"] == "recycle"]
        )
        number_remanufacture = len(
            timestep_result[timestep_result["component.state"] == "remanufacture"]
        )
        number_landfill = len(
            timestep_result[timestep_result["component.state"] == "landfill"]
        )
        total_components = len(timestep_result)
        report_list.append(
            {
                "ts": ts,
                "total_components": total_components,
                "fraction_use": number_use / total_components,
                "fraction_recycle": number_recycle / total_components,
                "fraction_remanufacture": number_remanufacture / total_components,
                "fraction_landfill": number_landfill / total_components,
            }
        )
    report_df = pd.DataFrame(report_list)
    return report_df


def make_plots(report_df, context):
    fig, axs = plt.subplots(nrows=4, ncols=2, figsize=(10, 7))
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.07, hspace=0.7)

    xs = report_df["ts"].values

    axs[0, 0].set_title("(a) Discrete Fraction Use")
    axs[0, 0].set_ylim(-0.1, 1.1)
    axs[0, 0].plot(xs, report_df["fraction_use"])

    axs[1, 0].set_title("(c) Discrete Fraction Remanufacture")
    axs[1, 0].set_ylim(-0.1, 1.1)
    axs[1, 0].plot(xs, report_df["fraction_remanufacture"])

    axs[2, 0].set_title("(e) Discrete Fraction Recycle")
    axs[2, 0].set_ylim(-0.1, 1.1)
    axs[2, 0].plot(xs, report_df["fraction_recycle"])

    axs[3, 0].set_title("(g) Discrete Fraction Landfill")
    axs[3, 0].set_ylim(-0.1, 1.1)
    axs[3, 0].set_xlabel("discrete timestep")
    axs[3, 0].plot(xs, report_df["fraction_landfill"])

    axs[0, 1].set_title("(b) SD Fraction Reus(ing)")
    axs[0, 1].set_ylim(-0.1, 1.1)
    axs[0, 1].plot(np.arange(len(context.fraction_reuse)), \
                   context.fraction_reuse, c="r")

    axs[1, 1].set_title("(d) SD Fraction Remanufactur(ing)")
    axs[1, 1].set_ylim(-0.1, 1.1)
    axs[1, 1].plot(np.arange(len(context.fraction_remanufacture)), \
                   context.fraction_remanufacture, c="r")

    axs[2, 1].set_title("(f) SD Fraction Recycl(ing)")
    axs[2, 1].set_ylim(-0.1, 1.1)
    axs[2, 1].plot(np.arange(len(context.fraction_remanufacture)),
                   context.fraction_recycle, c="r")

    axs[3, 1].set_title("(h) Discrete Fraction Landfill(ing)")
    axs[3, 1].set_ylim(-0.1, 1.1)
    axs[3, 1].set_xlabel("discrete timestep")
    axs[3, 1].plot(np.arange(len(context.fraction_remanufacture)),
                   context.fraction_landfill, c="r")

    plt.show()


def run_and_report():
    print(os.getcwd())
    context = Context("natl-wind-importable.py")
    context.populate_components("long_ten_usgs_dataset_materials.csv")
    component_log, material_component_log = context.run()
    report_df = report(component_log)
    make_plots(report_df, context)
    print("Writing component report...")
    report_df.to_csv("component_report.csv", index=False, float_format='%.3f')
    print("writing material component log...")
    material_component_log.to_csv("material_component_log.csv", index=False, float_format='%.3f')


if __name__ == "__main__":
    random.seed(0)
    run_and_report()
