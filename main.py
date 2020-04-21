from uuid import uuid4
from random import random, randint
import networkx as nx
from dataclasses import dataclass, field
import pysd
import pandas as pd
import numpy as np
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

    name: The name of this functional unit. This isn't a unique ID. It is
        the type of functional unit, such a s "turbine"

    lifespan: The current lifespan of this functional unit.

    node_id: The node_id of the current inventory that holds this functional
        unit.

    functional_unit_id: The unique ID for this functional unit. This unique
        ID does not rely on the name.

    The following three instance attributes are used together to determine if
    a unit should be landfilled, recycled, reused or remanufactured at each
    time step.

    rate_of_increasing_reuse_fraction
    rate_of_increasing_recycle_fraction
    rate_of_increasing_remanufacture_fraction

    sd_timesteps: pd.Series
        Each element is a value in SD timestep. The index on that element is the
        SimPy timestep that corresponds to it.
    """
    rate_of_increasing_reuse_fraction: pd.Series
    rate_of_increasing_recycle_fraction: pd.Series
    rate_of_increasing_remanufacture_fraction: pd.Series

    sd_timesteps: pd.Series

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
        action = self.disposal_action(env.now)
        if action == "reuse":
            print(f"{self.name} {self.functional_unit_id} is being EOLd at {env.now} is being reuse")
        elif action == "recycle":
            print(f"{self.name} {self.functional_unit_id} is being EOLd at {env.now} is being recycled")
        elif action == "remanufacture":
            print(f"{self.name} {self.functional_unit_id} is being EOLd at {env.now} is being remanufactured")
        else:
            print(f"{self.name} {self.functional_unit_id} is being EOLd at {env.now} and is going to landfill")

    def disposal_action(self, env_ts):
        """
        This method makes a decision about whether to recycle, resuse,
        or remanufacture at end of life.

        Parameters
        ----------
        env_ts: int
            The current timestep in the simulation.

        Returns
        -------
        str
            "reuse", "remanufacture", "recycle", "landfill" depending on the
            choice that is made.
        """

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

        sd_step = self.sd_timesteps[env_ts]

        reuse = self.rate_of_increasing_reuse_fraction[sd_step]
        recycle = self.rate_of_increasing_recycle_fraction[sd_step]
        remanufacture = self.rate_of_increasing_remanufacture_fraction[sd_step]

        if reuse == 0.0:
            return "reuse"
        elif recycle == 0.0:
            return "recycle"
        elif remanufacture == 0.0:
            return "remanufacture"
        else:
            return "landfill"


class Model:
    def __init__(self, model_fn):
        """
        The parameters set instance attributes of the same name.

        Parameters
        ----------
        model_fn:
            The function that is the SD model.
        """
        self.graph = nx.DiGraph()

        # The following instance attributes hold data from the SD model when it
        # is created.

        self.model = pysd.load(model_fn)
        self.normalized_recycle_favorability_over_linear = None
        self.rate_of_increasing_reuse_fraction = None
        self.rate_of_increasing_recycle_fraction = None
        self.rate_of_increasing_remamnufacture_fraction = None
        self.sd_timesteps = None

        # The simpy environment
        self.env = simpy.Environment()

    def run_sd_model(self):
        """
        This method runs the SD model to get the outputs we need to run
        the simulation.
        """
        result = self.model.run(return_columns=[
            'recycle_favorability_over_linear',
            'rate_of_increasing_reuse_fraction',
            'rate_of_increasing_recycle_fraction',
            'rate_of_increasing_reuse_fraction'
        ])

        self.sd_timesteps = result.index

        self.rate_of_increasing_recycle_fraction = result['rate_of_increasing_recycle_fraction']
        self.rate_of_increasing_remamnufacture_fraction = result['rate_of_increasing_recycle_fraction']
        self.rate_of_increasing_reuse_fraction = result['rate_of_increasing_reuse_fraction']

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

    def create_and_populate_inventories(self, min_eol=1, max_eol=400, min_inventory=20, max_inventory=20):
        """
        This creates functional units and populates inventories to their
        initial states.

        For this initial setup, there is a wind plant, recycler, remanufacturer,
        landfill, and wind plant. The "reuse" pathway is an edge that points
        back to the wind plant.

        The functional units are turbines.

        Parameters
        ----------
        min_eol:
            The minimum lifespan of a turbine in timesteps.

        max_eol:
            The maximum lifespan of a turbine in timesteps.

        min_inventory:
            The minimum number of turbines in an inventory.

        max_inventory:
            The maximum number of turbines in an inventory.
        """
        for node_id, inventory in self.graph.nodes(data="inventory"):
            if node_id not in ["landfill", "recycler", "remanufacturer"]:
                unit_count = randint(min_inventory, max_inventory)
                for _ in range(unit_count):
                    lifespan = randint(min_eol, max_eol)
                    unit = FunctionalUnit(name="Turbine",
                                          lifespan=lifespan,
                                          node_id=node_id,
                                          rate_of_increasing_recycle_fraction=\
                                            self.rate_of_increasing_recycle_fraction,
                                          rate_of_increasing_remanufacture_fraction=\
                                            self.rate_of_increasing_remamnufacture_fraction,
                                          rate_of_increasing_reuse_fraction=\
                                            self.rate_of_increasing_reuse_fraction,
                                          sd_timesteps=self.sd_timesteps)
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
        self.create_and_populate_inventories(min_inventory=50, max_inventory=50)
        self.env.run(until=len(self.sd_timesteps))
        # Commenting out because things aren't moving across the graph.
        # print(self.inventory_functional_units())


if __name__ == '__main__':
    app = Model("tinysd/tiny-sd_pysd_v30mar2020.py")
    app.run()
