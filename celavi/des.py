from typing import Dict, List, Callable

import simpy
import pandas as pd
import pysd  # type: ignore

from .inventory import FacilityInventory
from .component import Component
from .costgraph import CostGraph


class Context:
    """
    The Context class:

    - Provides the discrete time sequence for the model
    - Holds all the components in the model
    - Holds parameters for pathway cost models (dictionary)
    - Links the CostGraph to the DES model
    - Provides translation of years to timesteps and back again
    """

    def __init__(
        self,
        locations_filename: str,
        step_costs_filename: str,
        possible_items: List[str],
        cost_graph: CostGraph,
        cost_params: Dict = None,
        min_year: int = 2000,
        max_timesteps: int = 600,
        years_per_timestep: float = 0.0833,
        learning_by_doing_timesteps: int = 1
    ):
        """
        Parameters
        ----------
        step_costs_filename: str
            The pathname to the step_costs file that will determine the steps in
            each facility.

        cost_graph: CostGraph:
            The instance of the cost graph to use with this DES model.

        cost_params: Dict
            Dictionary of parameters for the learning-by-doing models and all
            other pathway cost models

        min_year: int
            The starting year of the model. Optional. If left unspecified
            defaults to 2000.

        max_timesteps: int
            The maximum number of discrete timesteps in the model. Defaults to
            200 or an end year of 2050.

        years_per_timestep: float
            The number of years covered by each timestep. Fractional
            values are allowed for timesteps that have a duration of
            less than one year. Default value is 0.25 or quarters (3 months).

        learning_by_doing_timesteps: int
            The number of timesteps that happen between each learning by
            doing recalculation.
        """

        self.cost_params = cost_params
        self.max_timesteps = max_timesteps
        self.min_year = min_year
        self.years_per_timestep = years_per_timestep

        self.components: List[Component] = []
        self.env = simpy.Environment()

        # Inventories hold the simple counts of materials at stages of
        # their lifecycle. The "component" inventories hold the counts
        # of whole components. The "material" inventories hold the mass
        # of those components.

        locations = pd.read_csv(locations_filename)
        step_costs = pd.read_csv(step_costs_filename)
        locations_step_costs = locations.merge(step_costs, on='facility_id')

        self.mass_facility_inventories = {}
        self.count_facility_inventories = {}
        for _, row in locations_step_costs.iterrows():
            facility_type = row['facility_type']
            facility_id = row['facility_id']
            step = row['step']
            step_facility_id = f"{step}_{facility_id}"
            self.mass_facility_inventories[step_facility_id] = FacilityInventory(
                facility_id=facility_id,
                facility_type=facility_type,
                step=step,
                possible_items=possible_items,
                timesteps=max_timesteps,
                processing_steps=[],  # TODO: Put real data here
                quantity_unit="tonne",
                can_be_negative=False
            )
            self.count_facility_inventories[step_facility_id] = FacilityInventory(
                facility_id=facility_id,
                facility_type=facility_type,
                step=step,
                possible_items=possible_items,
                timesteps=max_timesteps,
                processing_steps=[],  # TODO: Put real data here
                quantity_unit="count",
                can_be_negative=False
            )

        # initialize dictionary to hold pathway costs over time
        self.cost_history = {'year': [],
                             'landfilling cost': [],
                             'recycling to clinker cost': [],
                             'recycling to raw material cost': [],
                             'blade removal cost, per tonne': [],
                             'blade removal cost, per blade': [],
                             'blade mass, tonne': [],
                             'coarse grinding cost': [],
                             'fine grinding cost': [],
                             'segment transpo cost': [],
                             'landfill tipping fee': []}

        # initialize dictionary to hold transportation requirements
        self.transpo_eol = {'year': [],
                            'total eol transportation': []}

        # These are the costs from the learning by doing model
        self.learning_by_doing_costs = {
            "landfilling": 1.0,
            "recycle_to_clink_pathway": 2.0,
            "recycle_to_rawmat_pathway": 2.0
        }

        self.learning_by_doing_timesteps = learning_by_doing_timesteps

        self.cost_graph = cost_graph

    def years_to_timesteps(self, year: float) -> int:
        """
        Converts years into the corresponding timestep number of the discrete
        event model.

        Parameters
        ----------
        year: float
            The year can have a fractional part. The result of the conversion
            is rounding to the nearest integer.

        Returns
        -------
        int
            The discrete timestep that corresponds to the year.
        """

        return int(year / self.years_per_timestep)

    def timesteps_to_years(self, timesteps: int) -> float:
        """
        Converts the discrete timestep to a year.

        Parameters
        ----------
        timesteps: int
            The discrete timestep number. Must be an integer.

        Returns
        -------
        float
            The year converted from the discrete timestep.
        """
        return self.years_per_timestep * timesteps + self.min_year

    def populate(self, df: pd.DataFrame, lifespan_fns: Dict[str, Callable[[], float]]):
        """
        Before a model can run, components must be loaded into it. This method
        loads components from a DataFrame, has the following columns which
        correspond to the attributes of a component object:

        kind: str
            The type of component as a string. It isn't called "type" because
            "type" is a keyword in Python.

        year: float
            The year the component goes into use.

        mass_tonnes: float
            The mass of the component in tonnes.

        Each component is placed into a process that will timeout when the
        component begins its useful life, as specified in year. From there,
        choices about the component's lifecycle are made as further processes
        time out and decisions are made at subsequent timesteps.

        Parameters
        ----------
        df: pd.DataFrame
            The DataFrame which has components specified in the columns
            listed above.

        lifespan_fns: lifespan_fns: Dict[str, Callable[[], float]]
            A dictionary with the kind of component as the key and a Callable
            (probably a lambda function) that takes no arguments and returns
            a float as the value. When called, the value should return a value
            sampled from a probability distribution that corresponds to a
            predicted lifespan of the component. The key is used to call the
            value in a way similar to the following: lifespan_fns[row["kind"]]()
        """

        for _, row in df.iterrows():
            component = Component(
                kind=row["kind"],
                year=row["year"],
                mass_tonnes=row["mass_tonnes"],
                initial_facility_id=row["facility_id"],
                context=self,
                lifespan_timesteps=lifespan_fns[row["kind"]](),
            )
            self.env.process(component.begin_life(self.env))
            self.components.append(component)

    def average_blade_mass_tonnes(self, timestep):
        """
        Compute the average blade mass in tonnes for every blade in this
        context.

        Parameters
        ----------
        timestep: int
            The timestep at which this calculation is happening

        Returns
        -------
        float
            The average mass of the blade in tonnes.
        """
        total_blade_mass_eol = 0.0
        total_blade_count_eol = 0

        # # Calculate the total mass at EOL
        # total_blade_mass_eol += self.recycle_to_raw_material_inventory.transactions[timestep]["blade"]
        # total_blade_mass_eol += self.recycle_to_clinker_material_inventory.transactions[timestep]["blade"]
        # total_blade_mass_eol += self.landfill_material_inventory.transactions[timestep]["blade"]
        #
        # # Calculate the total count at EOL
        # total_blade_count_eol += self.recycle_to_raw_component_inventory.transactions[timestep]["blade"]
        # total_blade_count_eol += self.recycle_to_clinker_component_inventory.transactions[timestep]["blade"]
        # total_blade_count_eol += self.landfill_component_inventory.transactions[timestep]["blade"]

        for mass_inventory in self.mass_facility_inventories.values():
            total_blade_mass_eol += mass_inventory.transactions[timestep]["blade"]

        for count_inventory in self.count_facility_inventories.values():
            total_blade_count_eol += count_inventory.transactions[timestep]["blade"]

        # Return the average mass for all the blades.
        if total_blade_count_eol > 0:
            return total_blade_mass_eol / total_blade_count_eol
        else:
            return 1

    # def learning_by_doing_process(self, env):
    #     """
    #     This method contains a SimPy process that runs the learning-by-doing
    #     model on a periodic basis.
    #     """
    #     while True:
    #         yield env.timeout(self.learning_by_doing_timesteps)
    #         avg_blade_mass = self.average_blade_mass_tonnes(env.now)
    #         print('at timestep ', env.now, ', average blade mass is ', avg_blade_mass, ' tonnes\n')
    #         # This is a workaround. Make the learning by doing pathway costs
    #         # tolerant of a 0 mass for blades retired.
    #         if avg_blade_mass > 0:
    #             self.learning_by_doing(env.now, avg_blade_mass)

    def run(self) -> Dict[str, Dict[str, FacilityInventory]]:
        """
        This method starts the discrete event simulation running.

        Returns
        -------
        Dict[str, pd.DataFrame]
            A dictionary of inventories mapped to their cumulative histories.
        """
        # Schedule learning by doing timesteps (this will happen after all
        # other events have been scheduled)
        # self.env.process(self.learning_by_doing_process(self.env))

        self.env.run(until=int(self.max_timesteps))

        result = {
            "count_facility_inventories": self.count_facility_inventories,
            "mass_facility_inventories": self.mass_facility_inventories
        }

        return result
