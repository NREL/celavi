"""
Circular Economy Lifecycle Analysis and VIsualization, CELAVI

This file performs data I/O, preprocessing, and calls modules to perform a
complete CELAVI model run and save results.

Authors: Rebecca Hanes, Alicia Key, Tapajyoti (TJ) Ghosh, Annika Eberle
"""

import argparse

from celavi.scenario import Scenario


PARSER = argparse.ArgumentParser(description="Execute CELAVI model")
PARSER.add_argument("--data", help="Path to the input and output data folder.")
PARSER.add_argument(
    "--casestudy", help="Name of case study config file in data folder."
)
PARSER.add_argument(
    "--scenario", help="Name of scenario-specific config file in the data folder."
)

if __name__ == "__main__":
    Scenario(parser=PARSER)
