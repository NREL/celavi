import pysd
import networkx as nx
import pandas as pd
import numpy as np
from random import random


class App:
    def __init__(self, model_fn):
        self.model = pysd.load(model_fn)

        # Most of these are set in run_model_and_create_functions() below
        self.max_iterations = None
        self.timesteps = None
        self.normalized_recycle_favorability_over_linear = None

    def run_model_and_create_functions(self):
        result = self.result = self.model.run(return_columns=[
            'recycle_favorability_over_linear'
        ])
        self.timesteps = result.index

        recycle_favorability_over_linear = result['recycle_favorability_over_linear']

        # I am 100% sure I am abusing this column by nomralizing it, but I needed a
        # value between 0.0 and 1.0 to determine the probablity that something would
        # be recycled.

        normalized_recycle_favorability_over_linear = \
            (recycle_favorability_over_linear - recycle_favorability_over_linear.min()) / (recycle_favorability_over_linear.max() - recycle_favorability_over_linear.min())

        self.normalized_recycle_favorability_over_linear = \
            pd.Series(normalized_recycle_favorability_over_linear, index=self.timesteps, )

    def recycle_yes_or_no(self, ts):
        threshold = self.normalized_recycle_favorability_over_linear[ts]
        return random() < threshold  # Higher favorability less likely to recycle

    def run(self):
        self.run_model_and_create_functions()
        print(self.recycle_yes_or_no(1.25))


if __name__ == '__main__':
    app = App("tinysd/tiny-sd_pysd_v30mar2020.py")
    app.run()
