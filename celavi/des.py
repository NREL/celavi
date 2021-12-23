from typing import Dict, List, Callable, Union, Tuple
from math import floor, ceil
from datetime import datetime
import time

import simpy
import pandas as pd

from celavi.inventory import FacilityInventory
from celavi.transportation_tracker import TransportationTracker
from celavi.component import Component
from celavi.costgraph import CostGraph

from celavi.pylca_celavi.des_interface import pylca_run_main


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
        component_material_masses_filename: str,
        possible_components: List[str],
        possible_materials: List[str],
        cost_graph: CostGraph,
        cost_graph_update_interval_timesteps: int,
        path_dict: Dict = None,
        min_year: int = 2000,
        max_timesteps: int = 600,
        timesteps_per_year: int = 12
    ):
        """
        Parameters
        ----------
        step_costs_filename: str
            The pathname to the step_costs file that will determine the steps in
            each facility.

        component_material_masses_filename: str
            The pathname to the file that contains the average component masses.

        possible_components: List[str]
            The list of possible items (like "blade", "turbine", "foundation")

        possible_materials: List[str]
            The possible materials in the components. This should span all
            component types.

        cost_graph: CostGraph:
            The instance of the cost graph to use with this DES model.

        cost_graph_update_interval_timesteps: int
            Update the cost graph every n timesteps.

        path_dict: Dict
            Dictionary of parameters for the learning-by-doing models and all
            other pathway cost models

        min_year: int
            The starting year of the model. Optional. If left unspecified
            defaults to 2000.

        max_timesteps: int
            The maximum number of discrete timesteps in the model. Defaults to
            200 or an end year of 2050.

        timesteps_per_year: int
            The number of timesteps in one year. Default value is 12 timesteps
            per year, corresponding to a monthly model resolution.
        """

        self.path_dict = path_dict
        self.max_timesteps = max_timesteps
        self.min_year = min_year
        self.timesteps_per_year = timesteps_per_year

        self.components: List[Component] = []
        self.env = simpy.Environment()

        # Read the average component masses as an array. Then turn it into a
        # dictionary that maps integer years to component masses.
        # File data is total component mass per technology unit
        self.component_material_mass_tonne_dict: Dict[str, Dict[int, float]] = {}
        component_material_masses_df = pd.read_csv(component_material_masses_filename)

        for material in possible_materials:
            self.component_material_mass_tonne_dict[material] = {}
        for _, row in component_material_masses_df.iterrows():
            year = row['year']
            material = row['material']
            self.component_material_mass_tonne_dict[material][year] = row['mass_tonnes']

        self.possible_materials = possible_materials

        # Inventories hold the simple counts of materials at stages of
        # their lifecycle. The "component" inventories hold the counts
        # of whole components. The "material" inventories hold the mass
        # of those components.

        locations = pd.read_csv(locations_filename)
        step_costs = pd.read_csv(step_costs_filename)

        # After this merge, there will be "facility_type_x" and
        # "facility_type_y" columns
        locations_step_costs = locations.merge(step_costs, on='facility_id')

        self.count_facility_inventories = {}
        self.transportation_trackers = {}
        self.mass_facility_inventories = {}

        for _, row in locations_step_costs.iterrows():
            facility_type = row['facility_type_x']
            facility_id = row['facility_id']
            step = row['step']
            step_facility_id = f"{step}_{facility_id}"

            self.count_facility_inventories[step_facility_id] = FacilityInventory(
                facility_id=facility_id,
                facility_type=facility_type,
                step=step,
                possible_items=possible_components,
                timesteps=max_timesteps,
                quantity_unit="count",
                can_be_negative=False
            )

            self.mass_facility_inventories[step_facility_id] = FacilityInventory(
                facility_id=facility_id,
                facility_type=facility_type,
                step=step,
                possible_items=possible_materials,
                timesteps=max_timesteps,
                quantity_unit="tonnes",
                can_be_negative=False
            )

            self.transportation_trackers[step_facility_id] = TransportationTracker(timesteps=max_timesteps)

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

        return int(year * self.timesteps_per_year)

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
        return timesteps / self.timesteps_per_year + self.min_year

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
            year = row["year"]
            mass_tonnes = {
                material: self.component_material_mass_tonne_dict[material][year]
                for material in self.possible_materials
            }

            component = Component(
                kind=row["kind"],
                year=year,
                manuf_facility_id=row["manuf_facility_id"],
                in_use_facility_id=row["in_use_facility_id"],
                context=self,
                lifespan_timesteps=lifespan_fns[row["kind"]](),
                mass_tonnes=mass_tonnes
            )
            self.env.process(component.bol_process(self.env))
            self.components.append(component)

    def cumulative_mass_for_component_in_process_at_timestep(self,
                          component_kind: str,
                          process_name: List[str],
                          timestep: int):
        """
        Calculate the cumulative mass at a certain time of a given component
        passed through processes that contain the given name.

        For example, if you want to find cumulative component mass passed
        through coarse grinding facilities at time step 100, this is your
        method!

        Note: This uses the average component mass for the year, not the sum
        of facility inventories.

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
        year = int(ceil(self.timesteps_to_years(timestep)))
        avg_component_mass = self.average_total_component_mass_for_year(year)
        cumulative_counts = [
            facility.cumulative_input_history[component_kind][timestep]
            for name, facility in self.count_facility_inventories.items()
            if any(pname in name for pname in process_name)
        ]
        total_count = sum(cumulative_counts)
        total_mass = total_count * avg_component_mass
        print(f'{datetime.now()} process_name {process_name}, kind {component_kind}, time {timestep}, total_mass {total_mass} tonnes')
        return total_mass

    def pylca_interface_process(self, env):
        """
        pylca_interface_process() runs periodically to update the LCIA model with
        results from the DES model. It updates the LCA code with the latest distance
        and mass flow calculations.

        It only calls the LCA code for timesteps where the mass_kg > 0. Years with
        zero mass flows are not passed to the LCA.

        Parameters
        ----------
        env: Environment
            The SimPy environment this process belongs to.
        """
        while True:
            print(f'{datetime.now()} In While loop pylca interface', flush=True)
            time0 = time.time()
            yield env.timeout(self.timesteps_per_year)
            print(str(time.time() - time0) + ' yield of env timeout pylca took these many seconds')

            annual_data_for_lci = []
            window_last_timestep = env.now
            window_first_timestep = window_last_timestep - self.timesteps_per_year
            time0 = time.time()
            year = int(ceil(self.timesteps_to_years(env.now)))

            for facility_name, facility in self.mass_facility_inventories.items():
                process_name, facility_id = facility_name.split("_")
                for material in self.possible_materials:
                    annual_transactions = facility.transaction_history.loc[
                                          window_first_timestep:window_last_timestep + 1, material
                                          ]
                    positive_annual_transactions = annual_transactions[annual_transactions > 0]
                    mass_tonnes = positive_annual_transactions.sum()
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

            for facility_name, tracker in self.transportation_trackers.items():
                _, facility_id = facility_name.split("_")
                annual_transportations = tracker.inbound_tonne_km[window_first_timestep:window_last_timestep + 1]
                tonne_km = annual_transportations.sum()
                if tonne_km > 0:
                    row = {
                        'flow quantity': tonne_km,
                        'stage': 'Transportation',
                        'year': year,
                        'material': 'transportation',
                        'flow unit': 't * km',
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

    def average_total_component_mass_for_year(self, year):
        """
        Totals the masses of all materials in a component for a given year.

        Parameters
        ----------
        year: float
            The floating point year. Will be rounded to nearest integer year with
            int() and ceil()

        Returns
        -------
        float
            Average total component mass for a year.
        """
        year_int = int(ceil(year))
        total_mass = 0.0
        for material in self.possible_materials:
            total_mass += self.component_material_mass_tonne_dict[material][year_int]
        return total_mass

    def update_cost_graph_process(self, env):
        """
        This is the SimPy process that updates the cost graph periodically.
        """
        print('Updating cost graph')
        while True:
            print(f'{datetime.now()} In While loop update cost graph',flush = True)
            time0 = time.time()            
            yield env.timeout(self.cost_graph_update_interval_timesteps)
            print(str(time.time() - time0) + ' yield of env timeout costgraph took these many seconds')
            year = self.timesteps_to_years(env.now)

            _path_dict = self.path_dict.copy()
            _path_dict['year'] = year
            _path_dict['component mass'] = self.average_total_component_mass_for_year(year)

            for key in self.path_dict['learning'].keys():
                _path_dict['learning'][key]['cumul'] = \
                    self.cumulative_mass_for_component_in_process_at_timestep(
                        component_kind=_path_dict['learning'][key]['component'],
                        process_name=_path_dict['learning'][key]['steps'],
                        timestep=env.now
                    )
            self.cost_graph.update_costs(_path_dict)

            print(f"{datetime.now()} Updated cost graph {year}", flush=True)

    def run(self) -> Dict[str, FacilityInventory]:
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
        return self.count_facility_inventories
