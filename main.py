import pysd
import networkx as nx
import pandas as pd


class App:
    def __init__(self, model_fn):
        self.model = pysd.load(model_fn)

    def run(self):
        print("Hello world")


if __name__ == '__main__':
    app = App("tinysd/tiny-sd_pysd_v30mar2020.py")
    app.run()
