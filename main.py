import networkx as nx
from uuid import uuid4
from dataclasses import dataclass, field
import pysd
import pandas as pd
from random import random, randint
import simpy


pd.set_option('display.max_rows', 1000)


def unique_identifer_str():
    return str(uuid4())


@dataclass
class FunctionalUnit:
    normalized_recycle_favorability_over_linear: pd.Series
    name: str
    lifespan: int
    node_id: str
    functional_unit_id: str = field(default_factory=unique_identifer_str)

    def eol_me(self, env):
        yield env.timeout(self.lifespan)
        will_recycle = self.recycle_yes_or_no(env.now)
        if will_recycle:
            print(f"{self.name} {self.functional_unit_id} is being EOLd at {env.now} is being recycled")
        else:
            print(f"{self.name} {self.functional_unit_id} is being EOLd at {env.now} and is going to landfill")

    def recycle_yes_or_no(self, env_ts):
        threshold = self.normalized_recycle_favorability_over_linear.iloc[env_ts]
        return random() < threshold  # Higher favorability means less likely to recycle


class App:
    def __init__(self, model_fn, min_eol=1, max_eol=400, min_inventory=1, max_inventory=10, number_of_inventories=10):
        self.model = pysd.load(model_fn)
        self.min_eol = min_eol
        self.max_eol = max_eol
        self.min_inventory = min_inventory
        self.max_inventory = max_inventory
        self.number_of_inventories = number_of_inventories
        self.graph = nx.DiGraph()
        self.max_iterations = None
        self.timesteps = None
        self.normalized_recycle_favorability_over_linear = None
        self.env = simpy.Environment()

    def run_sd_model(self):
        result = self.model.run(return_columns=[
            'recycle_favorability_over_linear'
        ])
        self.timesteps = result.index


        # This makes it possible for a pathway to be implemented, but what determines
        # which pathway will be implemented is
        #
        # Look at 3 circularity pathways. Pick the lowest value pathway. And, in the unit
        # track which one it has been on before. You can't reuse twice in a row. You
        # can't remanufacture twice in a row. Never two non rcucling payhways next to
        # each other.
        #
        # If non linearity is possible, one of the following parameters is non-zero
        #
        # 1. Rate of increasing resuse fraction
        # 2. Rate of increasing recycling fraction
        # 3. Rate of increasing remanufacture fraction
        #
        # If non are non-zero choose the landfill.

        recycle_favorability_over_linear = result['recycle_favorability_over_linear']

        # I am 100% sure I am abusing this column by normalizing it, but I needed a
        # value between 0.0 and 1.0 to determine the probability that something would
        # be recycled.

        normalized_recycle_favorability_over_linear = \
            (recycle_favorability_over_linear - recycle_favorability_over_linear.min()) / (recycle_favorability_over_linear.max() - recycle_favorability_over_linear.min())

        self.normalized_recycle_favorability_over_linear = \
            pd.Series(normalized_recycle_favorability_over_linear, index=self.timesteps, )

    def create_and_populate_inventories(self):
        self.graph.add_node("recycler", inventory=[])
        self.graph.add_node("landfill", inventory=[])

        for i in range(self.number_of_inventories):
            inventory_id = f"inventory {i}"
            self.graph.add_node(inventory_id, inventory=[])
            self.graph.add_edge(inventory_id, "recycler", destination="recycler")
            self.graph.add_edge(inventory_id, "landfill", destination="landfill")

        for node_id, inventory in self.graph.nodes(data="inventory"):
            if node_id not in ["landfill", "recycler"]:
                unit_count = randint(self.min_inventory, self.max_inventory)
                for _ in range(unit_count):
                    lifespan = randint(self.min_eol, self.max_eol)
                    unit = FunctionalUnit(name="Turbine",
                                          lifespan=lifespan,
                                          node_id=node_id,
                                          normalized_recycle_favorability_over_linear= \
                                            self.normalized_recycle_favorability_over_linear)
                    self.env.process(unit.eol_me(self.env))
                    inventory.append(unit)

    def inventory_functional_units(self):
        rows = []
        for node_id, node in self.graph.nodes.data():
            for unit in node["inventory"]:
                rows.append({
                    "Inventory": node_id,
                    "Unit name": unit.name,
                    "Unit lifespan": unit.lifespan,
                    "Unit ID": unit.functional_unit_id
                })
        result = pd.DataFrame(rows)
        return result

    def run(self):
        self.run_sd_model()
        self.create_and_populate_inventories()
        self.env.run(until=400)
        print(self.inventory_functional_units())
        # Now run the environment


if __name__ == '__main__':
    app = App("tinysd/tiny-sd_pysd_v30mar2020.py")
    app.run()
