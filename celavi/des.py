from typing import Dict, List, Callable
from math import floor
from datetime import datetime
import time

import simpy
import pandas as pd
import numpy as np

from celavi.inventory import FacilityInventory
from celavi.transportation_tracker import TransportationTracker
from celavi.component import Component
from celavi.costgraph import CostGraph
from celavi.pylca_celavi.des_interface import PylcaCelavi


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
        lca: PylcaCelavi,
        cost_graph_update_interval_timesteps: int,
        path_dict: Dict = None,
        min_year: int = 2000,
        end_year: int = 2050,
        max_timesteps: int = 600,
        timesteps_per_year: int = 12,
        model_run : int = 0,
        verbose : int = 0
    ):
        """
        Parameters
        ----------
        locations_filename : str
            Path to the processed facility locations dataset.

        step_costs_filename: str
            Path to the step_costs dataset that determines the process steps in
            each facility.

        component_material_masses_filename: str
            Path to the dataset specifying component composition (materials and
            masses) over time.

        possible_components: List[str]
            The list of possible technology components.

        possible_materials: List[str]
            The possible materials in the components. This should span all
            component types.

        cost_graph: CostGraph
            The CostGraph instance to use with this Context instance.

        lca: PylcaCelavi
            The pyLCIA instance to use with this Context instance.

        cost_graph_update_interval_timesteps: int
            Frequency at which the process costs within the CostGraph instance are
            re-calculated.

        path_dict: Dict
            Dictionary of parameters for the learning-by-doing models and all
            other pathway cost models. The structure and content of this dictionary
            will vary by case study and is specified in the Scenario configuration
            file.

        min_year: int
            Simulation start (calendar) year. Optional. If left unspecified
            defaults to 2000.

        max_timesteps: int
            The maximum number of discrete timesteps in the simulation. Defaults
            to 200 or an end year of 2050.

        timesteps_per_year: int
            The number of timesteps in one simulation year. Default value is 12
            timesteps per year, corresponding to a monthly model resolution.

        model_run : int
            Model run identifier

        verbose: int
           toggle print statements of LCA mass available and calculation steps   
           0 = no prints. 1 = all prints. 
        """

        self.model_run = model_run
        self.path_dict = path_dict
        self.max_timesteps = max_timesteps
        self.min_year = min_year
        self.end_year = end_year
        self.timesteps_per_year = timesteps_per_year

        self.components: List[Component] = []
        self.env = simpy.Environment()

        # The top level dictionary has a key for each material type. The dictionaries
        # at the next level down have an integer key for each year of the DES run.
        # The values on these second-level dictionaries are the mass per component
        # for that material in that year.

        self.component_material_mass_tonne_dict: Dict[str, Dict[int, float]] = {}
        component_material_masses_df = pd.read_csv(component_material_masses_filename)

        for material in possible_materials:
            self.component_material_mass_tonne_dict[material] = {}
        for _, row in component_material_masses_df.iterrows():
            year = row["year"]
            material = row["material"]
            self.component_material_mass_tonne_dict[material][year] = row["mass_tonnes"]

        self.possible_materials = possible_materials

        # Inventories hold the simple counts of materials at stages of
        # their lifecycle. The "component" inventories hold the counts
        # of whole components. The "material" inventories hold the mass
        # of those components.

        self.count_facility_inventories = {}
        self.transportation_trackers = {}
        self.mass_facility_inventories = {}

        # Read the locations and step costs to make the facility inventories
        locations = pd.read_csv(locations_filename)
        step_costs = pd.read_csv(step_costs_filename)

        # Find state level location information for each facility. This should
        # be in the region_id_2 column. Put this into a dictionary that maps
        # facility ids to states. This is so the LCA code can user per-state
        # electricity mixes. The integers are cast as strings because that
        # is how they will be looked up in the interface to the LCA code.

        self.facility_states = {
            str(row["facility_id"]): row["region_id_2"]
            for _, row in locations.iterrows()
        }

        # After this merge, there will be "facility_type_x" and
        # "facility_type_y" columns
        locations_step_costs = locations.merge(step_costs, on="facility_id")

        for _, row in locations_step_costs.iterrows():
            facility_type = row["facility_type_x"]
            facility_id = row["facility_id"]
            step = row["step"]
            step_facility_id = f"{step}_{facility_id}"

            self.count_facility_inventories[step_facility_id] = FacilityInventory(
                facility_id=facility_id,
                facility_type=facility_type,
                step=step,
                possible_items=possible_components,
                timesteps=max_timesteps,
                quantity_unit="count",
                can_be_negative=False,
            )

            self.mass_facility_inventories[step_facility_id] = FacilityInventory(
                facility_id=facility_id,
                facility_type=facility_type,
                step=step,
                possible_items=possible_materials,
                timesteps=max_timesteps,
                quantity_unit="tonnes",
                can_be_negative=False,
            )

            self.transportation_trackers[step_facility_id] = TransportationTracker(
                timesteps=max_timesteps
            )

        self.cost_graph = cost_graph
        self.lca = lca
        self.cost_graph_update_interval_timesteps = cost_graph_update_interval_timesteps

        self.data_for_lci: List[Dict[str, float]] = []
        self.verbose = verbose

    def years_to_timesteps(self, year: float) -> int:
        """
        Convert calendar year into the corresponding timestep of the discrete
        event model.

        Parameters
        ----------
        year: float
            The year can have a fractional part. The result of the conversion
            is rounding to the nearest integer.

        Returns
        -------
        int
            The DES timestep that corresponds to the year.
        """

        return int(year * self.timesteps_per_year)

    def timesteps_to_years(self, timesteps: int) -> float:
        """
        Convert the discrete DES timestep to a fractional calendar year.

        Parameters
        ----------
        timesteps: int
            The discrete timestep number. Must be an integer.

        Returns
        -------
        float
            The year converted from the discrete timestep.
        """
        result = timesteps / self.timesteps_per_year + self.min_year
        return result

    def populate(self, df: pd.DataFrame, lifespan_fns: Dict[str, Callable[[], float]]):
        """
        Before a model can run, components must be loaded into it. This method
        loads components from a DataFrame, has the following columns which
        correspond to the attributes of a component object:

        Each component is placed into a process that will timeout when the
        component begins its useful life, as specified in year. From there,
        choices about the component's lifecycle are made as further processes
        time out and decisions are made at subsequent timesteps.

        Parameters
        ----------
        df: pd.DataFrame
            The DataFrame which has components specified in the columns below.

            Columns:
                kind: str
                    The type of component as a string. It isn't called "type" because
                    "type" is a keyword in Python.

                year: float
                    The year the component goes into use.

                mass_tonnes: float
                    The mass of the component in tonnes.            

        lifespan_fns: Dict[str, Callable[[], float]]
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
                mass_tonnes=mass_tonnes,
            )
            self.env.process(component.bol_process(self.env))
            self.components.append(component)

    def cumulative_mass_for_component_in_process_at_timestep(
        self, component_kind: str, process_name: List[str], timestep: int
    ):
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

        year = int(floor(self.timesteps_to_years(timestep)))
        avg_component_mass = self.average_total_component_mass_for_year(year)

        cumulative_counts = [
            facility.cumulative_input_history[component_kind][timestep]
            for name, facility in self.count_facility_inventories.items()
            if any(pname in name for pname in process_name)
        ]
        total_count = sum(cumulative_counts)
        total_mass = total_count * avg_component_mass
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
            yield env.timeout(self.timesteps_per_year)

            annual_data_for_lci = []
            window_last_timestep = env.now
            window_first_timestep = env.now - self.timesteps_per_year

            year = int(floor(self.timesteps_to_years(env.now)))

            for facility_name, facility in self.mass_facility_inventories.items():
                process_name, facility_id = facility_name.split("_")
                for material in self.possible_materials:
                    annual_transactions = facility.transaction_history.loc[
                        window_first_timestep:window_last_timestep, material
                    ]
                    sliced_info = facility.transaction_history.loc[
                        window_first_timestep:window_last_timestep,
                        [material, "timestep"],
                    ].reset_index()

                    sliced_info["year"] = (
                        sliced_info["timestep"] / self.timesteps_per_year
                        + self.min_year
                    )
                    actual_year = int(
                        floor(
                            self.timesteps_to_years(
                                sliced_info["timestep"][self.timesteps_per_year // 2]
                            )
                        )
                    )
                    problematic_value = sliced_info[material][self.timesteps_per_year]

                    # A problematic value is when mass is reported in the last time step of a sliced dataframe
                    # which belongs to the next year. Generally this happens only for manufacturing.
                    if problematic_value > 0:
                        problem_year = int(
                            floor(
                                self.timesteps_to_years(
                                    sliced_info["timestep"][self.timesteps_per_year]
                                )
                            )
                        )
                        actual_year = actual_year + 1

                    # If the facility is NOT manufacturing, keep only positive transactions
                    if facility_name.find("manufacturing") == -1:
                        positive_annual_transactions = annual_transactions[
                            annual_transactions > 0
                        ]
                    else:
                        # If the facility IS manufacturing, use all of the transactions
                        positive_annual_transactions = annual_transactions
                    mass_tonnes = positive_annual_transactions.sum()

                    if mass_tonnes > 0:
                        sliced_info["facility_name"] = facility_name
                        sliced_info["facility_id"] = facility_id
                    mass_kg = mass_tonnes * 1000
                    if mass_kg > 0:
                        row = {
                            "flow quantity": mass_kg,
                            "stage": process_name,
                            "year": actual_year,
                            "material": material,
                            "flow unit": "kg",
                            "facility_id": facility_id,
                            "route_id": None,
                            "state": self.facility_states[facility_id],
                        }
                        self.data_for_lci.append(row)
                        annual_data_for_lci.append(row)
            for facility_name, tracker in self.transportation_trackers.items():
                _, facility_id = facility_name.split("_")
                # List of all inbound transportation amounts to this facility in the past window
                annual_transportations = tracker.inbound_tonne_km[
                    window_first_timestep : window_last_timestep + 1
                ]
                # Corresponding list of the routes along which the inbound transportation took place
                route_ids = tracker.route_id[
                    window_first_timestep : window_last_timestep + 1
                ]

                # Case 1: There was no inbound transportation and the rest of this block is skipped
                # Provide no data to LCIA. Executes if none of the if/elif statements below are True.

                # Case 2: There was only one instance of inbound transportation
                # and therefore only one corresponding route
                if len(annual_transportations[annual_transportations != 0]) == 1:
                    # Provide one row of data to LCIA by filtering out zeros/Nones. No aggregation needed.
                    row = {
                        "flow quantity": annual_transportations[
                            annual_transportations != 0
                        ][0],
                        "stage": "Transportation",
                        "year": actual_year,
                        "material": "transportation",
                        "flow unit": "t * km",
                        "facility_id": facility_id,
                        "route_id": route_ids[annual_transportations != 0][0],
                        "state": self.facility_states[facility_id],
                    }
                    self.data_for_lci.append(row)
                    annual_data_for_lci.append(row)

                elif len(annual_transportations[annual_transportations != 0]) > 1:
                    # Case 3: There were multiple instances of inbound transportation that all took place along the same route
                    if len(np.unique(route_ids[annual_transportations != 0])) == 1:
                        # Provide one row of data to LCIA by summing the inbound transportation and filtering out Nones in route_ids.
                        row = {
                            "flow quantity": annual_transportations.sum(),
                            "stage": "Transportation",
                            "year": year,
                            "material": "transportation",
                            "flow unit": "t * km",
                            "facility_id": facility_id,
                            "route_id": route_ids[annual_transportations != 0][0],
                            "state": self.facility_states[facility_id],
                        }
                        self.data_for_lci.append(row)
                        annual_data_for_lci.append(row)
                    # Case 4: There were multiple instances of inbound transportation that took place along different routes
                    elif len(np.unique(route_ids[annual_transportations != 0])) > 1:
                        # Provide as many rows of data to LCIA as there are unique routes by filtering out zeros/Nones. Only
                        # aggregate if one or more routes had multiple instances of inbound transportation.
                        for _r in np.unique(route_ids[annual_transportations != 0]):
                            row = {
                                "flow quantity": annual_transportations[
                                    route_ids == _r
                                ].sum(),
                                "stage": "Transportation",
                                "year": year,
                                "material": "transportation",
                                "flow unit": "t * km",
                                "facility_id": facility_id,
                                "route_id": _r,
                                "state": self.facility_states[facility_id],
                            }
                            self.data_for_lci.append(row)
                            annual_data_for_lci.append(row)

            if annual_data_for_lci:
                if self.verbose == 1:
                    print(
                        f"{datetime.now()} pylca_interface_process(): Found flow quantities greater than 0, performing LCIA"
                    )
                df_for_pylca_interface = pd.DataFrame(annual_data_for_lci)
                self.lca.pylca_run_main(df_for_pylca_interface, self.verbose)
            else:
                if self.verbose == 1:
                  print(f"{datetime.now()} pylca_interface_process(): All Masses are 0")

    def average_total_component_mass_for_year(self, year):
        """
        Totals the masses of all materials in a component for a given year.

        Parameters
        ----------
        year: float
            The floating point year. Will be rounded to nearest integer year with
            int() and floor()

        Returns
        -------
        float
            Average total component mass for a year.
        """
        year = int(floor(year))
        total_mass = 0.0
        for material in self.possible_materials:
            total_mass += self.component_material_mass_tonne_dict[material][year]
        return total_mass

    def update_cost_graph_process(self, env):
        """
        This is the SimPy process that updates the cost graph periodically.
        """
        while True:
            yield env.timeout(self.cost_graph_update_interval_timesteps)

            year = self.timesteps_to_years(env.now)

            if year < self.end_year:
                _path_dict = self.path_dict.copy()
                _path_dict["year"] = year
                _path_dict[
                    "component mass"
                ] = self.average_total_component_mass_for_year(year)

                for key in self.path_dict["learning"].keys():
                    _path_dict["learning"][key][
                        "cumul"
                    ] = self.cumulative_mass_for_component_in_process_at_timestep(
                        component_kind=_path_dict["learning"][key]["component"],
                        process_name=_path_dict["learning"][key]["steps"],
                        timestep=env.now,
                    )
                self.cost_graph.update_costs(_path_dict)

    def run(self) -> Dict[str, FacilityInventory]:
        """
        This method executes the discrete event simulation.

        Returns
        -------
        Dict[str, pd.DataFrame]
            A dictionary of inventories mapped to their cumulative histories.
        """

        self.env.process(self.update_cost_graph_process(self.env))
        self.env.process(self.pylca_interface_process(self.env))
        self.env.run(until=int(self.max_timesteps))
        return self.count_facility_inventories
