from dataclasses import dataclass, field
from collections import OrderedDict
from typing import Dict, List, Callable, Optional
from random import randint
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import pysd  # type: ignore
import simpy  # type: ignore
from uuid import uuid4


def unique_identifer_str():
    """
    This returns a UUID that can serve as a unique identifier for anything.
    These UUIDs can be used as keys in a set or hash if needed.

    TODO: Replace this with an incrementing integer.

    Returns
    -------
    str
        A UUID to be used as a unique identifier.
    """
    return str(uuid4())


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

    process_function: Optional[Callable]
        A callable (in other words, a function) that can be called
        to process an entry into a state, such as a manufacture, landfill,
        or remanufacture process.
    """

    state: str
    lifespan_min: int = 40
    lifespan_max: int = 80
    process_function: Optional[Callable] = None

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


class Inventory:
    def __init__(self, quantity_unit: str = "tonne"):
        """
        The inventory class holds an inventory of materials and quantities
        for a landfill, virgin material extraction, or recycled material
        availability

        Parameters
        ----------
        quantity_unit: str
            The unit in which the quantity is recorded.


        Other instance variables
        ------------------------
        materials: Dict[str, int]
           The key of the dictionary is a string that is the name of the
           material. The value is an integer that is the quantity of the
           material.

        self.materials_history: OrderedDict[int, Dict[str, int]]:
            A history of the levels of the materials each time
            a deposit or withdrawal is made. It is an OrderedDict to
            ensure that keys are iterated in the same order they are
            inserted.
        """
        self.quantity_unit = quantity_unit
        self.component_materials: Dict[str, float] = {}
        self.component_materials_history: OrderedDict[
            int, Dict[str, float]
        ] = OrderedDict()

    def increment_material_quantity(
        self, material: str, quantity: float, timestep: int
    ) -> float:
        """
        Changes the material quantity in this inventory. If the material
        is not already present, then it is added to the inventory at a
        quantity of 0 before it is incremented.

        For virgin material extractions, the quantity should be negative
        to indicate a withdrawal.

        For landfill additions, the quantity should be positive to
        indicate a deposit of material.

        For recycling, the quantity can either be positive or negative,
        depending on if there is an increase in supply or a decrease in
        supply through consumption.

        Parameters
        ----------
        material: str
            The material being deposited or withdrawn

        quantity: int
            The quantity of the material, either positive or negative.

        timestep: int
            The timestep of this deposit or withdrawal or deposit
            (depending on the sign the quantity)

        Returns
        -------
        int
            The new quantity of the material.
        """
        if material not in self.component_materials:
            self.component_materials[material] = 0
        self.component_materials[material] += quantity
        copy_of_materials = {}
        for k, v in self.component_materials.items():
            copy_of_materials[k] = v
        self.component_materials_history[timestep] = copy_of_materials
        return self.component_materials[material]

    def check_material(self, material: str, threshold: int) -> bool:
        """
        Check to see if a material is present in a particular quantity.

        If the amount of material is greater than at_least, then it returns
        True. Otherwise it returns False.

        The use case for this is generally for using recycled material

        Parameters
        ----------
        material: str
            The name of the material in question.

        threshold: int
            The minimum amount of material being tested for.
        """
        if material not in self.component_materials:
            return False
        else:
            return self.component_materials[material] <= threshold


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
        self, sd_model_filename: str, year_intercept: float, years_per_timestep
    ):
        """
        For converting from discrete timesteps to years, the formula is
            year_intercept + timestep * years_per_timestep.

        Parameters
        ----------
        sd_model_filename: str
            The filename that has the PySD model.

        year_intercept: float
            The intercept for timestep to year conversion

        years_per_timestep: float
            The number of years per timestep for timestep conversion.
        """
        sd_model = pysd.load(sd_model_filename)
        sd = sd_model.run()
        self.sd_variables = sd.columns
        time_series = sd[
            ["Fraction Recycle", "Fraction Remanufacture", "Fraction Reuse"]
        ]
        self.fraction_recycle = time_series["Fraction Recycle"].values
        self.fraction_remanufacture = time_series["Fraction Remanufacture"].values
        self.fraction_reuse = time_series["Fraction Reuse"].values
        self.year_intercept = year_intercept
        self.years_per_timestep = years_per_timestep

        self.fraction_landfill = (
            1.0
            - self.fraction_recycle
            - self.fraction_reuse
            - self.fraction_remanufacture
        )

        self.env = simpy.Environment()
        self.components: List[Component] = []
        self.turbines: List[Turbine] = []

        self.component_material_event_log_list: List[Dict] = []

        self.virgin_material_inventory = Inventory()
        self.landfill_material_inventory = Inventory()

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
        return len(self.fraction_reuse)

    @staticmethod
    def choose_transition(component_material, ts: int) -> str:
        """
        Does not support landfilling at the present time.

        Does not use sophisticated decision making at this time.

        Does not keep track of the number of times it has been remanufactured

        HELP WANTED: How can I use the SD model to make more informed decisions
           about what to do with the SD model to capture better state
           transition decisions. I am still using probability distributions
           and this has been flagged as an area for improvement.
        """
        if component_material.state == "recycle":
            return "manufacturing"
        elif component_material.state == "manufacture":
            return "using"
        elif component_material.state == "reuse":
            return np.random.choice(["recycling", "landfilling"])
        elif component_material.state == "remanufacture":
            return "using"
        else:  # "use" state
            return np.random.choice(
                ["reusing", "recycling", "remanufacturing", "landfilling"]
            )

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

                single_component = turbine_df.query("Component == @component_type")
                for _, material_row in single_component.iterrows():
                    material_type = material_row["Material"]
                    material_tonnes = material_row["Material Tonnes"]
                    component_material = ComponentMaterial(
                        material_type=material_type,
                        context=self,
                        material_tonnes=material_tonnes,
                        component_material=f"{component_type} {material_type}",
                        lifespan=component_material_lifespan,
                        parent_component=component,
                    )
                    component.component_materials.append(component_material)
                    self.env.process(component_material.eol_process(self.env))

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

            for component in self.components:
                for material in component.component_materials:
                    self.component_material_event_log_list.append(
                        {
                            "ts": env.now,
                            "year": year,
                            "turbine_id": material.parent_component.parent_turbine.turbine_id,
                            "state": material.state,
                            "component_material_id": material.component_material_id,
                            "component_material": material.component_material,
                            "material_type": material.material_type,
                            "material_tonnes": material.material_tonnes,
                            "latitude": material.parent_component.parent_turbine.latitude,
                            "longitude": material.parent_component.parent_turbine.longitude,
                        }
                    )

    def run(self) -> pd.DataFrame:
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
        return material_component_log_df


class ComponentMaterial:
    """
    ComponentMaterial models a particular material in a specific component
    """

    def __init__(
        self,
        parent_component,  # Should be of type Component not defined yet.
        context: Context,
        component_material: str,
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

        component_material: str
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
            unique_identifer_str()
            if component_material_id is None
            else component_material_id
        )
        self.parent_component = parent_component
        self.context = context
        self.component_material = component_material
        self.material_type = material_type
        self.material_tonnes = material_tonnes
        self.lifespan = lifespan
        self.state = state
        self.transition_list: List[str] = []

        # The reuse and remanufacture counters
        self.reuse_counter = 0
        self.remanufacture_counter = 0

        self.transitions_table = {
            # Outbound use states
            StateTransition(state="use", transition="landfilling"): NextState(
                state="landfill",
                lifespan_min=1000,
                lifespan_max=1000,
                process_function=self.landfill,
            ),
            StateTransition(state="use", transition="reusing"): NextState(
                state="reuse", lifespan_min=40, lifespan_max=80
            ),
            StateTransition(state="use", transition="recycling"): NextState(
                state="recycle", lifespan_min=4, lifespan_max=4
            ),
            StateTransition(state="use", transition="remanufacturing"): NextState(
                state="remanufacture",
                lifespan_min=4,
                lifespan_max=4,
                process_function=self.remanufacture,
            ),
            # Outbound reuse states
            StateTransition(state="reuse", transition="ramnufacturing"): NextState(
                state="remanufacture",
                lifespan_min=4,
                lifespan_max=4,
                process_function=self.remanufacture,
            ),
            StateTransition(state="reuse", transition="landfilling"): NextState(
                state="landfill",
                lifespan_min=1000,
                lifespan_max=1000,
                process_function=self.landfill,
            ),
            StateTransition(state="reuse", transition="recycling"): NextState(
                state="recycle", lifespan_min=4, lifespan_max=4
            ),
            # Recycle outbound
            StateTransition(state="recycle", transition="manufacturing"): NextState(
                state="manufacture",
                lifespan_min=4,
                lifespan_max=4,
                process_function=self.manufacture,
            ),
            # Remanufacture outbound
            StateTransition(state="remanufacture", transition="using"): NextState(
                state="use",
                lifespan_min=40,
                lifespan_max=80,
                process_function=self.remanufacture,
            ),
            # Manufacture outbound
            StateTransition(state="manufacture", transition="using"): NextState(
                state="use", lifespan_min=40, lifespan_max=80
            ),
            # Landfill outbound
            StateTransition(state="landfill", transition="manufacturing"): NextState(
                state="manufacture",
                lifespan_min=4,
                lifespan_max=8,
                process_function=self.manufacture,
            ),
        }

        # When the component material is initialized, it will be initialized
        # into a particular state. Record the transition into this initial
        # state here.

        if self.state == "use":
            self.transition_list.append("using")
        elif self.state == "remanufacture":
            self.transition_list.append("remanufacturing")
        elif self.state == "recycle":
            self.transition_list.append("recycling")
        elif self.state == "manufacture":
            self.transition_list.append("manufacturing")
        elif self.state == "reuse":
            self.transition_list.append("reusing")

    @staticmethod
    def manufacture(context: Context, component_material, timestep: int):
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
        component_material.reuse_counter = 0
        component_material.remanufacture_counter = 0
        context.virgin_material_inventory.increment_material_quantity(
            material=component_material.component_material,
            quantity=-component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def remanufacture(context: Context, component_material, timestep: int):
        """
        Remanufactures the component material by incrementing its
        remanufacture counter.
        """
        print(
            f"Remanufacture process component_material {component_material.component_material_id}"
        )
        component_material.remanufacture_counter += 1

    @staticmethod
    def landfill(context: Context, component_material, timestep: int):
        """
        Landfills a component material by incrementing the material in the
        landfill.
        """
        print(
            f"Landfill process component_material {component_material.component_material_id}"
        )
        context.landfill_material_inventory.increment_material_quantity(
            material=component_material.component_material,
            quantity=component_material.material_tonnes,
            timestep=timestep,
        )

    @staticmethod
    def reuse(context: Context, component_material, timestep: int):
        """
        Reuses a component material by incrementing its reuse counter
        """
        print(
            f"Reuse process component_material {component_material.component_material_id}"
        )
        component_material.reuse_counter += 1

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
        if next_state.process_function is not None:
            next_state.process_function(self.context, self, timestep)

        # Check to see if this component material was landfilled because this
        # is a special case. In that case, the component material should
        # immediately pass into the manufacture state to build a replacement.

        if self.state == "landfill":
            lookup = StateTransition(state=self.state, transition="manufacturing")
            manufacture_state = self.transitions_table[lookup]
            self.state = manufacture_state.state
            self.lifespan = manufacture_state.lifespan
            self.transition_list.append("manufacturing")
            process_function = manufacture_state.process_function
            process_function(self.context, self, timestep)

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
