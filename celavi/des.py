from typing import Dict, List, Callable, Union, Tuple
from math import floor, ceil
from datetime import datetime
import time

import simpy
import pandas as pd

from celavi.inventory import FacilityInventory
from celavi.component import Component
from celavi.costgraph import CostGraph

from pylca_celavi.des_interface import pylca_run_main


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
        avg_blade_masses_filename: str,
        possible_items: List[str],
        cost_graph: CostGraph,
        cost_graph_update_interval_timesteps: int,
        cost_params: Dict = None,
        min_year: int = 2000,
        max_timesteps: int = 600,
        years_per_timestep: float = 0.0833
    ):
        """
        For the average_blade_masses file, the columns are "p_year" and "Glass Fiber:Blade"
        for the year and the average amount of glass fiber in each blade, respectively.

        Parameters
        ----------
        step_costs_filename: str
            The pathname to the step_costs file that will determine the steps in
            each facility.

        avg_blade_masses_filename: str
            The pathname to the file that contains the average blade masses.

        possible_items: List[str]
            The list of possible items (like "blade", "turbine", "foundation")

        cost_graph: CostGraph:
            The instance of the cost graph to use with this DES model.

        cost_graph_update_interval_timesteps: int
            Update the cost graph every n timesteps.

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
        """

        self.cost_params = cost_params
        self.max_timesteps = max_timesteps
        self.min_year = min_year
        self.years_per_timestep = years_per_timestep

        self.components: List[Component] = []
        self.env = simpy.Environment()

        # Read the average blade masses as an array. Then turn it into a dictionary
        # that maps integer years to glass fiber blade masses.
        avg_blade_masses_df = pd.read_csv(avg_blade_masses_filename)
        self.avg_blade_mass_tonnes_dict = {
            int(row['year']): float(row['Glass Fiber:Blade'])
            for _, row in avg_blade_masses_df.iterrows()
        }

        # Inventories hold the simple counts of materials at stages of
        # their lifecycle. The "component" inventories hold the counts
        # of whole components. The "material" inventories hold the mass
        # of those components.

        locations = pd.read_csv(locations_filename)
        step_costs = pd.read_csv(step_costs_filename)

        # After this merge, there will be "facility_type_x" and
        # "facility_type_y" columns
        locations_step_costs = locations.merge(step_costs, on='facility_id')

        self.mass_facility_inventories = {}
        self.count_facility_inventories = {}
        for _, row in locations_step_costs.iterrows():
            facility_type = row['facility_type_x']
            facility_id = row['facility_id']
            step = row['step']
            step_facility_id = f"{step}_{facility_id}"
            self.mass_facility_inventories[step_facility_id] = FacilityInventory(
                facility_id=facility_id,
                facility_type=facility_type,
                step=step,
                possible_items=possible_items,
                timesteps=max_timesteps,
                quantity_unit="tonne",
                can_be_negative=False
            )
            self.count_facility_inventories[step_facility_id] = FacilityInventory(
                facility_id=facility_id,
                facility_type=facility_type,
                step=step,
                possible_items=possible_items,
                timesteps=max_timesteps,
                quantity_unit="count",
                can_be_negative=False
            )

        self.cost_graph = cost_graph
        self.cost_graph_update_interval_timesteps = cost_graph_update_interval_timesteps

        self.data_for_lci: List[Dict[str, float]] = []

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
                initial_facility_id=row["facility_id"],
                context=self,
                lifespan_timesteps=lifespan_fns[row["kind"]](),
            )
            self.env.process(component.manufacturing(self.env))
            self.components.append(component)

    def cumulative_mass_for_component_in_process_at_timestep(self,
                          component_kind: str,
                          process_name: str,
                          timestep: int):
        """
        Calculate the cumulative mass at a certain time of a given component
        passed through processes that contain the given name.

        For example, if you want to find cumulative masses of blades passed
        through coarse grinding facilities at time step 100, this is your
        method!

        Parameters
        ----------
        component_kind: str
            The kind of component (such as "blade" passing through an inventory)

        process_name: str
            The process name (such as "fine griding") to look for in the facility
            inventory names.

        timestep: int
            The time, in timestep, to calculate the cumulative inventory for.

        Returns
        -------
        float
            Total cumulative mass of the component in the process at the
            timestep.
        """
        cumulative_masses = [
            inventory.cumulative_history['blade'][timestep]
            for name, inventory in self.mass_facility_inventories.items()
            if process_name in name
        ]
        total_mass = sum(cumulative_masses)
        print(f'{datetime.now()} process_name {process_name}, kind {component_kind}, time {timestep}, total_mass {total_mass}')
        return total_mass

    def pylca_interface_process(self, env):
        timesteps_per_year = 12
        component = 'blade'
        material = 'glass fiber reinforced polymer'
        while True:
            print(f'{datetime.now()}In While loop pylca interface',flush = True)
            time0 = time.time()
            yield env.timeout(timesteps_per_year)   # Run annually
            print(str(time.time() - time0) + ' yield of env timeout pylca took these many seconds')


            annual_data_for_lci = []
            window_last_timestep = env.now
            window_first_timestep = window_last_timestep - timesteps_per_year
            time0 = time.time()
            year = int(ceil(self.timesteps_to_years(env.now)))
            for facility_name, facility in self.count_facility_inventories.items():
                process_name, facility_id = facility_name.split("_")
                annual_transactions = facility.transaction_history.loc[window_first_timestep:window_last_timestep + 1, component]
                positive_annual_transactions = annual_transactions[annual_transactions > 0]
                # TODO: Correct input data instead of dividing by 3.0
                mass_tonnes = positive_annual_transactions.sum() * self.avg_blade_mass_tonnes_dict[year] / 3.0
                mass_kg = mass_tonnes * 1000
                if mass_kg > 0:
                    row = {
                        'flow quantity': mass_kg,
                        'stage': process_name,
                        'year': year,
                        'material': material,
                        'flow unit': 'kg',
                        'facility_id': facility_id
                    }
                    self.data_for_lci.append(row)
                    annual_data_for_lci.append(row)
            print(str(time.time() - time0)+' For loop of pylca took these many seconds')
            if len(annual_data_for_lci) > 0:
                print(f'{datetime.now()} DES interface: Found flow quantities greater than 0, performing LCIA')
                df_for_pylca_interface = pd.DataFrame(annual_data_for_lci)
                pylca_run_main(df_for_pylca_interface)
            else:
                print(f'{datetime.now()} DES interface: All Masses are 0')
                

    def update_cost_graph_process(self, env):
        """
        This is the SimPy process that updates the cost graph periodically.
        """
        print('Updating cost graph')
        while True:
            print(f'{datetime.now()}In While loop update cost graph',flush = True)
            time0 = time.time()            
            yield env.timeout(self.cost_graph_update_interval_timesteps)
            print(str(time.time() - time0) + ' yield of env timeout costgraph took these many seconds')
            year = self.timesteps_to_years(env.now)
            year_int = round(year)
            avg_blade_mass_kg = self.avg_blade_mass_tonnes_dict[year_int] * 1000

            cum_mass_coarse_grinding = self.cumulative_mass_for_component_in_process_at_timestep(
                component_kind='blade',
                process_name='coarse grinding',
                timestep=env.now
            )

            cum_mass_fine_grinding = self.cumulative_mass_for_component_in_process_at_timestep(
                component_kind='blade',
                process_name='fine grinding',
                timestep=env.now
            )

            self.cost_graph.update_costs(
                year=year,
                blade_mass=avg_blade_mass_kg,
                finegrind_cumul=cum_mass_fine_grinding,
                coarsegrind_cumul=cum_mass_coarse_grinding,
                verbose=0
            )

            print(f"{datetime.now()} Updated cost graph {year}: cum_mass_fine_grinding {cum_mass_fine_grinding}, cum_mass_coarse_grinding {cum_mass_coarse_grinding}, avg_blade_mass_kg {avg_blade_mass_kg}",flush = True)

    def run(self) -> Dict[str, Dict[str, FacilityInventory]]:
        """
        This method starts the discrete event simulation running.

        Returns
        -------
        Dict[str, pd.DataFrame]
            A dictionary of inventories mapped to their cumulative histories.
        """

        print('DES RUN STARTING\n\n\n',flush=True)
        
        self.env.process(self.update_cost_graph_process(self.env))
        self.env.process(self.pylca_interface_process(self.env))

        self.env.run(until=int(self.max_timesteps))

        result = {
            "count_facility_inventories": self.count_facility_inventories,
            "mass_facility_inventories": self.mass_facility_inventories
        }

        return result
