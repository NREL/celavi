from tinylca.state_machine_units_model import Context
from typing import List, Dict
import pandas as pd
import matplotlib.pyplot as plt
import random


def report(result):
    max_timestep = int(result["ts"].max())
    report_list: List[Dict] = []
    for ts in range(1, max_timestep + 1):
        timestep_result = result[result["ts"] == ts]
        number_use = len(timestep_result[timestep_result["unit.state"] == "use"])
        number_recycle = len(
            timestep_result[timestep_result["unit.state"] == "recycle"]
        )
        number_remanufacture = len(
            timestep_result[timestep_result["unit.state"] == "remanufacture"]
        )
        number_landfill = len(
            timestep_result[timestep_result["unit.state"] == "landfill"]
        )
        total_units = len(timestep_result)
        report_list.append(
            {
                "ts": ts,
                "total_units": total_units,
                "fraction_use": number_use / total_units,
                "fraction_recycle": number_recycle / total_units,
                "fraction_remanufacture": number_remanufacture / total_units,
                "fraction_landfill": number_landfill / total_units,
            }
        )
    report_df = pd.DataFrame(report_list)
    return report_df


def make_plots(report_df, context):
    fig, axs = plt.subplots(nrows=4, ncols=2, figsize=(7, 7))
    plt.tight_layout()

    xs = report_df["ts"].values

    axs[0, 0].set_title("Discrete Fraction Use")
    axs[0, 0].set_ylim(-0.1, 1.1)
    axs[0, 0].plot(xs, report_df["fraction_use"])

    axs[1, 0].set_title("Discrete Fraction Remanufacture")
    axs[1, 0].set_ylim(-0.1, 1.1)
    axs[1, 0].plot(xs, report_df["fraction_remanufacture"])

    axs[2, 0].set_title("Discrete Fraction Recycle")
    axs[2, 0].set_ylim(-0.1, 1.1)
    axs[2, 0].plot(xs, report_df["fraction_recycle"])

    axs[3, 0].set_title("Discrete Fraction Landfill")
    axs[3, 0].set_ylim(-0.1, 1.1)
    axs[3, 0].plot(xs, report_df["fraction_landfill"])

    plt.show()


def run_and_report():
    context = Context("tinysd/vensim model/national-scale/natl-wind-importable.py")
    context.populate_units()
    result = context.run()
    report_df = report(result)
    make_plots(report_df, context)
    report_df.to_csv("circular-revolution.csv")


if __name__ == "__main__":
    random.seed(0)
    run_and_report()
