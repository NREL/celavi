import pysd
import networkx as nx
import pandas as pd


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

        pd.set_option('display.max_rows', 500)
        pd.set_option('display.max_columns', 500)
        pd.set_option('display.width', 1000)

        print(result.describe())


if __name__ == '__main__':
    app = App("tinysd/tiny-sd_pysd_v30mar2020.py")
    app.run()
