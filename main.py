from uuid import uuid4
from random import random, randint
import networkx as nx
from dataclasses import dataclass, field
import pysd
import pandas as pd
import simpy


pd.set_option('display.max_rows', 1000)


def unique_identifer_str():
    """
    This returns a UUID that can serve as a unique identifier for anything

    Returns
    -------
    str
        A UUID to be used as a unique identifer.
    """
    return str(uuid4())


@dataclass
class FunctionalUnit:
    """
    The instance attributes are:

    normalized_recycle_favorability_over_linear: The time series of the
        favorability of recycling versus landfilling.

    name: The name of this functional unit. This isn't a unique ID. It is
        the type of functional unit, such a s "turbine"

    lifespan: The current lifespan of this functional unit.

    node_id: The node_id of the current inventory that holds this functional
        unit.

    functional_unit_id: The unique ID for this functional unit. This unique
        ID does not rely on the name.
    """

    normalized_recycle_favorability_over_linear: pd.Series
    name: str
    lifespan: int
    node_id: str
    functional_unit_id: str = field(default_factory=unique_identifer_str)

    def eol_me(self, env):
        """
        This method is called by the SimPy environment when the lifespan
        times out.

        Parameters
        ----------
        env
            The SimPy environment.
        """
        yield env.timeout(self.lifespan)
        will_recycle = self.recycle_yes_or_no(env.now)
        if will_recycle:
            print(f"{self.name} {self.functional_unit_id} is being EOLd at {env.now} is being recycled")
        else:
            print(f"{self.name} {self.functional_unit_id} is being EOLd at {env.now} and is going to landfill")

    def recycle_yes_or_no(self, env_ts):
        """
        This method makes the decision about whether to recycle or landfill the
        unit at its end of life.
        """
        threshold = self.normalized_recycle_favorability_over_linear.iloc[env_ts]
        return random() < threshold  # Higher favorability means less likely to recycle


class Model:
    def __init__(self, model_fn, min_eol=1, max_eol=400, min_inventory=1, max_inventory=10):
        """
        The parameters set instance attributes of the same name.

        Parameters
        ----------
        model_fn:
            The function that is the SD model.

        min_eol:
            The minimum lifespan of a turbine in timesteps.

        max_eol:
            The maximum lifespan of a turbine in timesteps.

        min_inventory:
            The minimum number of turbines in an inventory.

        max_inventory:
            The maximum number of turbines in an inventory.
        """
        self.min_eol = min_eol
        self.max_eol = max_eol
        self.min_inventory = min_inventory
        self.max_inventory = max_inventory
        self.graph = nx.DiGraph()

        # The following instance attributes hold data from the SD model when it
        # is created.
        self.model = pysd.load(model_fn)
        self.normalized_recycle_favorability_over_linear = None
        self.timesteps = None

        # The simpy environment
        self.env = simpy.Environment()

    def run_sd_model(self):
        """
        This method runs the SD model to get the outputs we need to run
        the simulation.
        """
        result = self.model.run(return_columns=[
            'recycle_favorability_over_linear'
        ])
        self.timesteps = result.index


        # Look at 3 circularity pathways. Pick the lowest value pathway. And, in the unit
        # track which one it has been on before. You can't reuse twice in a row. You
        # can't remanufacture twice in a row. Never two non recycling pathways next to
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

    def create_graph(self):
        """
        This creates a graph of inventories waiting to be populated by the
        create_and_populate_inventories method.
        """
        self.graph.add_node("recycler", inventory=[])
        self.graph.add_node("landfill", inventory=[])
        self.graph.add_node("remanufacturer", inventory=[])
        self.graph.add_node("wind plant", inventory=[])
        self.graph.add_edge("wind plant", "recycler", event="recycle")
        self.graph.add_edge("wind plant", "landfill", event="landfill")
        self.graph.add_edge("wind plant", "remanufacturer", event="remanufacture")
        self.graph.add_edge("recycler", "remanufacturer", event="remanufacture")
        self.graph.add_edge("remanufacturer", "wind plant", event="deploy")

    def create_and_populate_inventories(self):
        """
        This creates functional units and populates inventories to their
        initial states.

        For this initial setup, there is a wind plant, recycler, remanufacturer,
        landfill, and wind plant. The "reuse" pathway is an edge that points
        back to the wind plant.

        The functional units are turbines.
        """
        for node_id, inventory in self.graph.nodes(data="inventory"):
            if node_id not in ["landfill", "recycler", "remanufacturer"]:
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
        """
        This creates a dataframe that is an inventory of the functional units
        and the inventories they are currently in.
        """
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
        self.create_graph()
        self.create_and_populate_inventories()
        self.env.run(until=400)
        print(self.inventory_functional_units())


if __name__ == '__main__':
    app = Model("tinysd/tiny-sd_pysd_v30mar2020.py")
    app.run()
