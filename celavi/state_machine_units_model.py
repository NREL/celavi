from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional, Tuple, Union
from random import randint
import pandas as pd  # type: ignore
import pysd  # type: ignore
import simpy  # type: ignore
from csv import DictWriter

from .inventory import Inventory
from .unique_identifier import UniqueIdentifier


@dataclass(frozen=True)
class StateTransition:
    """
    This class specifies the starting point for a transition in a state machine.

    StateTransition and NextState are used together in a state transition
    dictionary, where the key is a StateTransition instance and the
    value is a NextState instance.

    Instance attributes
    -------------------
    state: str
        The starting state in the state machine.

    transition: str
        The transition away from the current state.
    """

    state: str
    transition: str


@dataclass(frozen=True)
class NextState:
    """
    This class specifies the target for a state machine transition.

    StateTransition and NextState are used together in a state transition
    dictionary, where the key is a StateTransition instance and the
    value is a NextState instance.

    Instance attributes
    -------------------
    state: str
        The target state after the state transition.

    lifespan_min: int
        The minimum duration of the state in discrete timesteps.

    lifespan_max: int
        The maximum duration of the state in discrete timesteps.

    The following two instance attributes point to function that
    handle bookkeeping.

    state_entry_function: Optional[Callable]
        A callable (in other words, a function) that is called
        to process an entry into a state, such as a manufacture, landfill,
        or remanufacture process.

    state_exit_function: Optional[Callable]
        A callable that is called when a component material leaves the
        previous state.
    """

    state: str
    lifespan_min: int = 40
    lifespan_max: int = 80
    state_entry_function: Optional[Callable] = None
    state_exit_function: Optional[Callable] = None

    @property
    def lifespan(self) -> int:
        """
        This calculates a random integer for the duration of a state
        transition.

        Returns
        -------
        int
            The discrete timesteps until end-of-life or the lifespan
            of the state.
        """
        return (
            self.lifespan_min
            if self.lifespan_min == self.lifespan_max
            else randint(self.lifespan_min, self.lifespan_max + 1)
        )


class Context:
    """
    Context is a class that provides:

    1. A SimPy environment for discrete time steps.
    2. Storage components that are state machines
    3. An SD model to probabilistically control the state machines
    4. Lists of turbines, components, and component_materials
    5. The table of allowed state transitions.
    6. A way to translate discrete timesteps to years.
    """

    def __init__(
        self,
        sd_model_filename: str,
        component_material_state_log_filename: str,
        year_intercept: float,
        years_per_timestep,
        possible_component_materials: List[str],
    ):
        """
        For converting from discrete timesteps to years, the formula is
            year_intercept + timestep * years_per_timestep.

        Parameters
        ----------
        sd_model_filename: str
            The filename that has the PySD model.

        component_material_state_log_filename: str
            The log filename of the component material states.

        year_intercept: float
            The intercept for timestep to year conversion

        years_per_timestep: float
            The number of years per timestep for timestep conversion.
        """
        self.sd_model_run = pysd.load(sd_model_filename).run()
        self.sd_model_run.to_csv("celavi_sd_model.csv")
        timesteps = len(self.sd_model_run)
        self.year_intercept = year_intercept
        self.years_per_timestep = years_per_timestep
        self.component_material_state_log_filename = component_material_state_log_filename
        self.env = simpy.Environment()
        self.components: List[Component] = []
        self.turbines: List[Turbine] = []
        self.component_material_event_log_list: List[Dict] = []

        # Start the component material log

        self.component_material_event_log_fieldnames = [
            "ts",
            "year",
            "turbine_id",
            "state",
            "component_material_id",
            "component_material",
            "material_type",
            "material_tonnes",
            "latitude",
            "longitude",
        ]

        with open(component_material_state_log_filename, "w") as csvfile:
            writer = DictWriter(csvfile, self.component_material_event_log_fieldnames)
            writer.writeheader()

        # Setup all the inventories

        self.virgin_material_inventory = Inventory(
            name="virgin materials",
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
            can_be_negative=True,
        )
        self.landfill_material_inventory = Inventory(
            name="landfill",
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
            can_be_negative=False,
        )
        self.remanufacture_material_inventory = Inventory(
            name="remanufacture",
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
            can_be_negative=False,
        )
        self.use_material_inventory = Inventory(
            name="use",
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
            can_be_negative=False,
        )
        self.remanufacture_material_inventory = Inventory(
            name="remanufacture",
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
            can_be_negative=False,
        )
        self.reuse_material_inventory = Inventory(
            name="reuse",
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
            can_be_negative=False,
        )
        self.recycle_material_inventory = Inventory(
            name="recycle",
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
            can_be_negative=False,
        )
        self.manufacture_material_inventory = Inventory(
            name="manufacture",
            possible_component_materials=possible_component_materials,
            timesteps=timesteps,
            can_be_negative=False,
        )

    @property
    def max_timestep(self) -> int:
        """
        This returns the maximum timestep available. It is a count of the number
        of timesteps in the SD run.

        Returns
        -------
        int
            The maximum timestep.
        """
        return len(self.sd_model_run)

    def choose_transition(self, component_material, ts: int) -> str:
        """
        Makes choices about lifecycle events.
        """

        # The current choice is landfill versus recycle
        cost_of_landfilling = self.sd_model_run["cost of landfilling"].values
        recycle_process_cost = self.sd_model_run["recycle process cost"].values
        remanufacture_process_cost = self.sd_model_run[
            "remanufacture process cost"
        ].values
        reuse_process_cost = self.sd_model_run["reuse process cost"]

        if component_material.state == "recycle":
            return "manufacturing"
        elif component_material.state == "manufacture":
            return "using"
        elif component_material.state == "landfill":
            # This isn't landfill mining--landfilled component materials need
            # to be replenished through manufacturing.
            return "manufacturing"
        else:  # "use" state
            return (
                "landfilling"
                if cost_of_landfilling[ts] <= recycle_process_cost[ts]
                else "recycling"
            )

        # TODO: Put in reuse, recycle, remanufacture pathways

    def populate_components(self, turbine_data_filename: str) -> None:
        """
        This makes an initial population of components in the
        model.

        Parameters
        ----------
        turbine_data_filename: str
            The .csv file that has the data to populate the model.
        """
        all_turbines = pd.read_csv(turbine_data_filename)
        turbine_ids = all_turbines["id"].unique()
        for turbine_id in turbine_ids:
            print(f"Importing turbine {turbine_id}...")
            turbine_df = all_turbines.query("id == @turbine_id")
            latitude = turbine_df["ylat"].values[0]
            longitude = turbine_df["xlong"].values[0]
            turbine = Turbine(
                turbine_id=turbine_id, latitude=latitude, longitude=longitude
            )
            self.turbines.append(turbine)
            component_types = turbine_df["Component"].unique()
            for component_type in component_types:
                component = Component(
                    component_type=component_type, context=self, parent_turbine=turbine,
                )
                self.components.append(component)
                turbine.components.append(component)

                component_material_lifespan = randint(40, 80)
                # component_material_lifespan = 10

                single_component = turbine_df.query("Component == @component_type")
                for _, material_row in single_component.iterrows():
                    material_type = material_row["Material"]
                    material_tonnes = material_row["Material Tonnes"]
                    component_material = ComponentMaterial(
                        material_type=material_type,
                        context=self,
                        material_tonnes=material_tonnes,
                        name=f"{component_type} {material_type}",
                        lifespan=component_material_lifespan,
                        parent_component=component,
                        state="use",
                    )
                    component.component_materials.append(component_material)
                    self.env.process(component_material.eol_process(self.env))
        return

    def log_process(self, env):
        """
        This is a SimPy process that logs the state of every component at every
        timestep.

        Parameters
        ----------
        env: simpy.Environment
            The SimPy environment which can be used to generate timeouts.
        """
        while True:
            print(f"Logging {env.now}...")
            yield env.timeout(1)
            year = self.year_intercept + env.now * self.years_per_timestep
            component_material_log_for_timestep = []

            for component in self.components:
                for material in component.component_materials:
                    component_material_log_for_timestep.append(
                        {
                            "ts": env.now,
                            "year": year,
                            "turbine_id": material.parent_component.parent_turbine.turbine_id,
                            "state": material.state,
                            "component_material_id": material.component_material_id,
                            "component_material": material.name,
                            "material_type": material.material_type,
                            "material_tonnes": material.material_tonnes,
                            "latitude": material.parent_component.parent_turbine.latitude,
                            "longitude": material.parent_component.parent_turbine.longitude,
                        }
                    )

            with open(self.component_material_state_log_filename, "a") as csvfile:
                writer = DictWriter(csvfile, self.component_material_event_log_fieldnames)
                writer.writerows(component_material_log_for_timestep)

    def concatenate_inventory_cumulative_logs(self):
        """
        Concatenates all the cumulative history logs from all the inventories.
        """

        # First, make a series of years
        years: List[float] = []
        for timestep in range(len(self.sd_model_run)):
            years.append(self.year_intercept + timestep * self.years_per_timestep)
        years_series = pd.Series(years)

        # Now get all the inventories, and store them in a dictionary
        states = {
            "use": self.use_material_inventory.cumulative_history,
            "reuse": self.reuse_material_inventory.cumulative_history,
            "recycle": self.recycle_material_inventory.cumulative_history,
            "remanufacture": self.remanufacture_material_inventory.cumulative_history,
            "landfill": self.landfill_material_inventory.cumulative_history,
            "virgin_material": self.virgin_material_inventory.cumulative_history,
            "manufacture": self.manufacture_material_inventory.cumulative_history,
        }

        # Append the years column to all of them
        for state, cumulative_history in states.items():
            cumulative_history["Year"] = years_series.copy()
            cumulative_history["State"] = state

        # Concatenate the cumulative history dataframes
        concatenated = pd.concat(states.values())

        return concatenated

    def run(self) -> Tuple[pd.DataFrame, Union[pd.DataFrame, pd.Series]]:
        """
        This runs the model. Note that it does not initially populate the model
        first.

        Returns
        -------
        pd.DataFrame
            The log of the state every component_material at every step of the simulation.
        """
        self.env.process(self.log_process(self.env))
        self.env.run(self.max_timestep)
        material_component_log_df = pd.DataFrame(self.component_material_event_log_list)
        inventory_cumulative_logs = self.concatenate_inventory_cumulative_logs()
        return material_component_log_df, inventory_cumulative_logs


class ComponentMaterial:
    """
    ComponentMaterial models a particular material in a specific component
    """

    def __init__(
        self,
        parent_component,  # Should be of type Component not defined yet.
        context: Context,
        name: str,
        material_type: str,
        material_tonnes: float,
        lifespan: int,
        state: str = "use",
        component_material_id: str = None,
    ):
        """
        Parameters
        ----------
        parent_component: Component
            The component that contains this material_component

        material: str
            The name of the type of material.

        name: str
            The name of the component followed by the name of the material.

        component_material_id: str
            Optional. A unique identifying string for the material
            component. Will populate with a UUID if unspecified.

        Instance variables not in parameters
        ------------------------------------
        transitions_table: Dict[StateTransition, NextState]
                The dictionary that controls the state transitions.

        HELP WANTED: Are there any other states or transitions we should
        use int the state machine?
        """
        self.component_material_id = (
            UniqueIdentifier.unique_identifier()
            if component_material_id is None
            else component_material_id
        )
        self.parent_component = parent_component
        self.context = context
        self.name = name
        self.material_type = material_type
        self.material_tonnes = material_tonnes
        self.lifespan = lifespan
        self.state = state
        self.transition_list: List[str] = []

        # Setup the counters
        self.reuse_counter = 0
        self.remanufacture_counter = 0
        self.recycle_counter = 0

        self.transitions_table = {
            # Outbound use states
            StateTransition(state="use", transition="landfilling"): NextState(
                state="landfill",
                lifespan_min=1,
                lifespan_max=1,
                state_entry_function=self.landfill,
                state_exit_function=self.leave_use,
            ),
            StateTransition(state="use", transition="reusing"): NextState(
                state="reuse",
                lifespan_min=40,
                lifespan_max=40,
                state_entry_function=self.reuse,
                state_exit_function=self.leave_use,
            ),
            StateTransition(state="use", transition="recycling"): NextState(
                state="recycle",
                lifespan_min=1,
                lifespan_max=1,
                state_entry_function=self.recycle,
                state_exit_function=self.leave_use,
            ),
            StateTransition(state="use", transition="remanufacturing"): NextState(
                state="remanufacture",
                lifespan_min=1,
                lifespan_max=1,
                state_entry_function=self.remanufacture,
                state_exit_function=self.leave_use,
            ),
            # Outbound reuse states
            StateTransition(state="reuse", transition="ramnufacturing"): NextState(
                state="remanufacture",
                lifespan_min=1,
                lifespan_max=1,
                state_entry_function=self.remanufacture,
                state_exit_function=self.leave_reuse,
            ),
            StateTransition(state="reuse", transition="landfilling"): NextState(
                state="landfill",
                lifespan_min=1,
                lifespan_max=1,
                state_entry_function=self.landfill,
                state_exit_function=self.leave_reuse,
            ),
            StateTransition(state="reuse", transition="recycling"): NextState(
                state="recycle",
                lifespan_min=1,
                lifespan_max=1,
                state_entry_function=self.recycle,
                state_exit_function=self.leave_reuse,
            ),
            # Recycle outbound
            StateTransition(state="recycle", transition="manufacturing"): NextState(
                state="manufacture",
                lifespan_min=1,
                lifespan_max=1,
                state_entry_function=self.manufacture_recycled_material,
                state_exit_function=self.leave_recycle,
            ),
            # Remanufacture outbound
            StateTransition(state="remanufacture", transition="using"): NextState(
                state="use",
                lifespan_min=40,
                lifespan_max=40,
                state_entry_function=self.use,
                state_exit_function=self.leave_remanufacture,
            ),
            # Manufacture outbound
            StateTransition(state="manufacture", transition="using"): NextState(
                state="use",
                lifespan_min=40,
                lifespan_max=40,
                state_entry_function=self.use,
                state_exit_function=self.leave_manufacture,
            ),
            # Landfill outbound
            StateTransition(state="landfill", transition="manufacturing"): NextState(
                state="manufacture",
                lifespan_min=1,
                lifespan_max=1,
                state_entry_function=self.manufacture_virgin_material,
                # No state exit function here, because the manufacturing does
                # not mine the landfill; rather manufacturing extracts
                # virgin materials that are not in the landfill. See the
                # self.manufacture function
            ),
        }

        # When the component material is initialized, it will be initialized
        # into a particular state. Record the transition into this initial
        # state here. and place it into its initial inventory.

        if self.state == "use":
            self.transition_list.append("using")
            context.use_material_inventory.increment_material_quantity(
                component_material_name=name, quantity=material_tonnes, timestep=0,
            )
        elif self.state == "remanufacture":
            self.transition_list.append("remanufacturing")
            context.remanufacture_material_inventory.increment_material_quantity(
                component_material_name=name, quantity=material_tonnes, timestep=0,
            )
        elif self.state == "recycle":
            self.transition_list.append("recycling")
            context.recycle_material_inventory.increment_material_quantity(
                component_material_name=name, quantity=material_tonnes, timestep=0,
            )
        elif self.state == "reuse":
            self.transition_list.append("reusing")
            context.reuse_material_inventory.increment_material_quantity(
                component_material_name=name, quantity=material_tonnes, timestep=0,
            )
        else:
            raise ValueError(
                f"Component material {name} cannot be initialized into {self.state}"
            )

    @staticmethod
    def remanufacture(context: Context, component_material, timestep: int):
        """
        Remanufactures the component material by incrementing its
        remanufacture counter.
        """
        print(
            f"Remanufacture process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        component_material.remanufacture_counter += 1
        context.remanufacture_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def leave_remanufacture(context: Context, component_material, timestep: int):
        """
        This leaves the remanufacture of a component material by decrementing
        the counter.
        """
        print(
            f"Remanufacture process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        context.remanufacture_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=-component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def landfill(context: Context, component_material, timestep: int):
        """
        Landfills a component material by incrementing the material in the
        landfill.

        The landfill process is special because there is no corresponding
        leave_landfill method since component materials never leave the
        landfill.
        """
        print(
            f"Landfill process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        context.landfill_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def manufacture_virgin_material(
        context: Context, component_material, timestep: int
    ):
        """
        Manufactures the component referenced by component_material.

        It does this by withdrawing from the virgin materials
        inventory in the quantity listed in the component material.

        It also resets the reuse and remanufacture counters.

        Parameters
        ----------
        context: Context
            The context that has the virgin materials inventory

        component_material: ComponentMaterial
            The component_material that is to be manufactured.

        timestep: int
            The discrete timestep at which this is happening.
        """
        print(
            f"Manufacture from virgin material component_material {component_material.component_material_id}, timestep={timestep}"
        )
        component_material.reuse_counter = 0
        component_material.remanufacture_counter = 0

        context.virgin_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=-component_material.material_tonnes,
            timestep=timestep,
        )

        # Place the material into the manufacturing inventory
        context.manufacture_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def manufacture_recycled_material(
        context: Context, component_material, timestep: int
    ):
        """
        Manufactures from recycled material.

        TODO: Integrate the material manufacturing methods
        """
        print(
            f"Manufacture from recycled material component_material {component_material.component_material_id}, timestep={timestep}"
        )
        component_material.reuse_counter = 0
        component_material.remanufacture_counter = 0

        # Place the material into the manufacturing inventory
        context.manufacture_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def leave_manufacture(context: Context, component_material, timestep: int):
        """
        Pulls a component material out of the manufacturing inventory.
        """
        print(
            f"Leave manufacture process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        context.manufacture_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=-component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def reuse(context: Context, component_material, timestep: int):
        """
        Reuses a component material by incrementing its reuse counter
        """
        print(
            f"Reuse process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        component_material.reuse_counter += 1
        context.reuse_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def leave_reuse(context: Context, component_material, timestep: int):
        """
        This method leaves the reuse state of a component material
        """
        print(
            f"Leave reuse process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        component_material.reuse_counter += 1
        context.reuse_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=-component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def recycle(context: Context, component_material, timestep: int):
        """
        This recycles a component material
        """
        print(
            f"Recycle process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        component_material.recycle_counter += 1
        context.recycle_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def leave_recycle(context: Context, component_material, timestep: int):
        """
        This recycles a component material
        """
        print(
            f"Leave recycle process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        component_material.recycle_counter += 1
        context.recycle_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=-component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def use(context: Context, component_material, timestep: int):
        """
        This recycles a component material
        """
        print(
            f"Use process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        context.use_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def leave_use(context: Context, component_material, timestep: int):
        """
        This method decrements the use inventory when a component material leaves use.
        """
        print(
            f"Leave use process component_material {component_material.component_material_id}, timestep={timestep}"
        )
        context.use_material_inventory.increment_material_quantity(
            component_material_name=component_material.name,
            quantity=-component_material.material_tonnes,
            timestep=timestep,
        )

    def transition(self, transition: str, timestep: int) -> None:
        """
        Transition the component's state machine from the current state based on a
        transition.

        Parameters
        ----------
        transition: str
            The next state to transition into.

        timestep: int
            The discrete timestep.

        Returns
        -------
        None

        Raises
        ------
        KeyError
            Raises a KeyError if the transition is not accessible from the
            current state.
        """
        lookup = StateTransition(state=self.state, transition=transition)
        if lookup not in self.transitions_table:
            raise KeyError(
                f"transition: {transition} not allowed from current state {self.state}"
            )
        next_state = self.transitions_table[lookup]
        self.state = next_state.state
        self.lifespan = next_state.lifespan
        self.transition_list.append(transition)
        if next_state.state_entry_function is not None:
            next_state.state_entry_function(self.context, self, timestep)
        if next_state.state_exit_function is not None:
            next_state.state_exit_function(self.context, self, timestep)

    def eol_process(self, env):
        """
        This is a generator for the SimPy process that controls what happens
        when this component reaches the end of its lifespan. The duration of the
        timeout is controlled by this lifespan.

        Parameters
        ----------
        env: simpy.Environment
            The SimPy environment controlling the lifespan of this component.
        """
        while True:
            yield env.timeout(self.lifespan)
            next_transition = self.context.choose_transition(self, env.now)
            self.transition(next_transition, env.now)


@dataclass
class Turbine:
    """
    The Turbine class represents a turbine.

    Instance attributes
    -------------------
    turbine_id: str
        The identification string for the turbine, such as an FAA identifier.
        This should be unique.

    components: List[Component]
        The list of components that make this turbine.

    latitude: float
        The latitude of the turbine.

    longitude: float
        The longitude of the turbine.
    """

    turbine_id: str
    latitude: float
    longitude: float
    components: List = field(default_factory=list)  # list holds components


@dataclass
class Component:
    """
    This specifies a component within the model

    Instance attributes
    -------------------
    parent_turbine: Turbine
        The turbine that contains this component.

    context: Context
        The context that contains this turbine

    component_type: str
        The type of component (Nacelle, Tower, Blade)

    materials: List[ComponentMaterial]
        Optional. If left unspecified, it defaults to an empty list.
        The list of
    """

    context: Context
    component_type: str
    parent_turbine: Turbine
    component_materials: List[ComponentMaterial] = field(default_factory=list)
