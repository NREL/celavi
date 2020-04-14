import pysd
import networkx as nx
import pandas as pd
import numpy as np


class App:
    def __init__(self, model_fn):
        self.model = pysd.load(model_fn)

        # Most of these are set in run_model_and_create_functions() below
        self.recycling_probability = None
        self.max_iterations = None
        self.timesteps = None

    def run(self):
        self.run_model_and_create_functions()
        print("Hello world")

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

        print(normalized_recycle_favorability_over_linear.max())
        print(normalized_recycle_favorability_over_linear.min())


if __name__ == '__main__':
    app = App("tinysd/tiny-sd_pysd_v30mar2020.py")
    app.run()
