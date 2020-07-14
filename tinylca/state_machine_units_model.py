from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from random import randint
import numpy as np
import pandas as pd
import pysd
import simpy
from uuid import uuid4


def unique_identifer_str():
    """
    This returns a UUID that can serve as a unique identifier for anything.
    These UUIDs can be used as keys in a set or hash if needed.

    Returns
    -------
    str
        A UUID to be used as a unique identifier.
    """
    return str(uuid4())[-10:]


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
    """

    state: str
    lifespan_min: int = 40
    lifespan_max: int = 80

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
    4. A list of components.
    5. The table of allowed state transitions.
    6. A way to translate discrete timesteps to years.
    """
    def __init__(self, 
                 sd_model_filename: str, 
                 year_intercept: float, 
                 years_per_timestep):
        """
        TODO: Make docstirng
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

        self.fraction_landfill = 1.0 -\
            self.fraction_recycle -\
            self.fraction_reuse -\
            self.fraction_remanufacture

        self.env = simpy.Environment()
        self.components: List[Component] = []

        self.component_event_log_list: List[Dict] = []
        self.component_material_event_log_list: List[Dict] = []

        self.default_transitions_table = {
            StateTransition(state="use", transition="recycling"): NextState(
                state="recycle", lifespan_min=4, lifespan_max=8
            ),
            StateTransition(state="use", transition="reusing"): NextState(state="use"),
            StateTransition(state="use", transition="landfilling"): NextState(
                state="landfill", lifespan_min=1000, lifespan_max=1000
            ),
            StateTransition(state="use", transition="remanufacturing"): NextState(
                state="remanufacture", lifespan_min=4, lifespan_max=8
            ),
            StateTransition(state="recycle", transition="remanufacturing"): NextState(
                "remanufacture", lifespan_min=4, lifespan_max=8
            ),
            StateTransition(state="remanufacture", transition="using"): NextState(
                "use"
            ),
            StateTransition(state="landfill", transition="landfilling"): NextState(
                "landfill", lifespan_min=1000, lifespan_max=1000
            ),
        }

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

    # Could not make a type for component (it needs to be of type Unit) because component is
    # defined below context.
    def probabilistic_transition(self, component_material, ts: int) -> str:
        """
        This method is the link between the SD model and the discrete time
        model. It returns a string with the name of a state transition
        generated with probabilities from the SD model.

        Parameters
        ----------
        component: ComponentMaterial
            The component instance that is being transitioned

        ts: int
            The timestep in the discrete time model used to look up values from
            the SD model.

        Returns
        -------
        str
            The name of the transition to send to the component's state machine.
        """
        if component_material.state == "recycle":
            return "remanufacturing"
        elif component_material.state == "remanufacture":
            return "using"
        elif component_material.state == "landfill":
            return "landfilling"

        else:  # The "use" state

            # Do not choose "remanufacture" and "reuse" (or a combination of the two)
            # twice in a row. If this happens, give an even chance of recycling or
            # landfilling
            if component_material.transition_list[-1] == "reuse" \
                    or component_material.transition_list[-2:] == ['remanufacturing', 'remanufacturing']\
                    or component_material.transition_list[-2:] == ['reusing', 'remanufacturing']:
                choices = ["recycling", "landfilling"]
                choice = np.random.choice(choices)
                return choice

            else:
                probabilities = np.array([
                    self.fraction_recycle[ts],
                    self.fraction_remanufacture[ts],
                    self.fraction_reuse[ts],
                    self.fraction_landfill[ts]
                ])

                # Use this line to force probabilities for testing.
                # probabilities = np.array([0.0, 1.0, 0.0, 0.0])

                choices = ["recycling", "remanufacturing", "reusing", "landfilling"]
                choice = np.random.choice(choices, p=np.array(probabilities))
                return choice

    def populate_components(self, turbine_data_filename: str) -> None:
        """
        This makes an initial population of components in the
        model.
        """
        all_turbines = pd.read_csv(turbine_data_filename)
        turbine_ids = all_turbines["id"].unique()
        for turbine_id in turbine_ids:
            print(f"Importing turbine {turbine_id}...")
            single_turbine = all_turbines.query("id == @turbine_id")
            # TODO: Make the following two lines use .loc
            latitude = single_turbine.iloc[0, 18]
            longitude = single_turbine.iloc[0, 17]
            component_types = single_turbine["Component"].unique()
            for component_type in component_types:
                component = Component(
                    component_type=component_type,
                    latitude=latitude,
                    longitude=longitude,
                    context=self,
                )
                self.components.append(component)

                component_material_lifespan = randint(40, 80)

                single_component = single_turbine.query("Component == @component_type")
                for _, material_row in single_component.iterrows():
                    material_type = material_row["Material"]
                    material_tonnes = material_row["Material Tonnes"]
                    component_material = ComponentMaterial(
                        material_type=material_type,
                        context=self,
                        material_tonnes=material_tonnes,
                        component_material=f"{component_type} {material_type}",
                        latitude=latitude,
                        longitude=longitude,
                        lifespan=component_material_lifespan,
                        parent_component=component,
                        transitions_table=self.default_transitions_table,
                    )
                    component.materials.append(component_material)
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
                for material in component.materials:
                    self.component_material_event_log_list.append({
                        "ts": env.now,
                        "year": year,
                        "state": material.state,
                        "component_material_id": material.component_material_id,
                        "component_material": material.component_material,
                        "material_type": material.material_type,
                        "material_tonnes": material.material_tonnes,
                        "latitude": material.latitude,
                        "longitude": material.longitude,
                    })

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


class Component:
    """
    This models a component within the discrete time model.
    """

    def __init__(self,
                 component_type: str,
                 latitude: float,
                 longitude: float,
                 context: Context,
                 component_id: str = None):
        """
        Parameters
        ----------
        component_type: str
            The type of component this is (e.g., "turbine blade")

        latitude: float
            The latitude geolocation of this component.

        longitude: float
            The longitude geolocation of this component.

        context: Context
            The context (class from above) in which the component operates.

        component_id: str
            The unique identifier for the component. This doesn't rely on the
            type of component. If it is not overridden, it defaults to a UUID.

        Instance attributes that are not parameters
        -------------------------------------------
        self.transition_list: List[str]
            The list of state transition history. This is used to block
            disallowed sequences of transitions. This is a shortcut to
            keep our state transition tables simpler.

        self.materials: List[ComponentMaterial]
            This is the list of the materials inside the component.
        """

        self.component_type = component_type
        self.latitude = latitude
        self.longitude = longitude
        self.context = context
        self.component_id = str(uuid4()) if component_id is None else component_id
        self.transition_list = []
        self.materials = []

    def __str__(self):
        """
        A reasonable string representation of the component for use with print().
        """
        return f"type: {self.component_type}, id:{self.component_id}, state: {self.state}, lifespan:{self.lifespan}"


@dataclass
class ComponentMaterial:
    """
    This class stores a material in a component

    Instance attributes
    -------------------
    parent_component: Component
        The component that contains this material_component

    latitude: float
        The latitude location of this component

    longitude: float
        The longitude location of this component

    material: str
        The name of the type of material.

    component_material: str
        The name of the component followed by the name of the material.

    component_material_id: str
        Optional. A unique identifying string for the material
        component. Will populate with a UUID if unspecified.

    transitions_table: Dict[StateTransition, NextState]
            The dictionary that controls the state transitions.
    """
    parent_component: Component
    context: Context
    transitions_table: Dict[StateTransition, NextState]
    component_material: str
    material_type: str
    material_tonnes: float
    latitude: float
    longitude: float
    lifespan: int
    state: str = "use"
    transition_list: List[str] = field(default_factory=list)
    component_material_id: str = field(default_factory=unique_identifer_str)

    def __post_init__(self):
        if self.state == "use":
            self.transition_list.append("using")
        elif self.state == "remanufacture":
            self.transition_list.append("remanufacturing")
        elif self.state == "recycle":
            self.transition_list.append("recycling")

    def transition(self, transition: str) -> None:
        """
        Transition the component's state machine from the current state based on a
        transition.

        Parameters
        ----------
        transition: str
            The next state to transition into.

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
            next_transition = self.context.probabilistic_transition(self, env.now)
            self.transition(next_transition)

@dataclass
class Turbine:
    """
    TODO: Make docstring
    """
    latitude: float
    longitude: float
    components: List[Component] = field(default_factory=list)
