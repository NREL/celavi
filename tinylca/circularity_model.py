from dataclasses import dataclass, field
from typing import Dict, List
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

    Obviously, the
    """

    state: str
    lifespan_min: int = 40
    lifespan_max: int = 80

    @property
    def eol(self) -> int:
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
    2. Functional units that are state machines
    3. An SD model to probabilistically control the state machines
    4. A list of functional units.
    5. The table of allowed state transitions.
    """
    def __init__(self, sd_model_filename: str):
        sd_model = pysd.load(sd_model_filename)
        sd = sd_model.run()
        self.sd_variables = sd.columns
        time_series = sd[
            ["Fraction Recycle", "Fraction Remanufacture", "Fraction Reuse"]
        ]
        self.fraction_recycle = time_series["Fraction Recycle"].values
        self.fraction_remanufacture = time_series["Fraction Remanufacture"].values
        self.fraction_reuse = time_series["Fraction Reuse"].values
        self.env = simpy.Environment()
        self.log_list: List[Dict] = []
        self.units: List[Unit] = []

        self.transitions_table = {
            StateTransition(state="use", transition="recycling"): NextState(
                state="recycle"
            ),
            StateTransition(state="use", transition="reusing"): NextState(state="use"),
            StateTransition(state="use", transition="landfilling"): NextState(
                state="landfill", lifespan_min=1000, lifespan_max=1000
            ),
            StateTransition(state="use", transition="remanufacturing"): NextState(
                state="remanufacture"
            ),
            StateTransition(state="recycle", transition="remanufacturing"): NextState(
                "remanufacture"
            ),
            StateTransition(state="remanufacture", transition="using"): NextState(
                "use"
            ),
            StateTransition(state="landfill", transition="landfilling"): NextState(
                "landfill"
            ),
        }

    @property
    def log_df(self) -> pd.DataFrame:
        """
        This returns the log of each unit's state at each timestep.

        The dataframe has the following columns:

        ts: The discrete timestep of the log entry
        unit.unit_type: The type of the functional unit
        unit.unit_id: The uuid of the functional unit
        unit.state: The current state of the functional unit

        Returns
        -------
        pd.DataFrame
            The dataframe of the log.
        """
        result = pd.DataFrame(self.log_list)
        return result

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

    # Could not make a type for unit (it needs to be of type Unit) because unit is
    # defined below context.
    def probabilistic_transition(self, unit, ts: int) -> str:
        """
        This method is the link between the SD model and the discrete time
        model. It returns a string with the name of a state transition
        generated with probabilities from the SD model.

        Parameters
        ----------
        unit: Unit
            The functional unit instance that is being transitioned

        ts: int
            The timestep in the discrete time model used to look up values from
            the SD model.

        Returns
        -------
        str
            The name of the transition to send to the unit's state machine.
        """
        if unit.state == "recycle":
            return "remanufacturing"
        elif unit.state == "remanufacture":
            return "using"
        elif unit.state == "landfill":
            return "landfilling"
        else:
            circular_probabilities = np.array(
                [
                    self.fraction_recycle[ts],
                    self.fraction_remanufacture[ts],
                    self.fraction_reuse[ts],
                ]
            )
            landfill_probability = 1.0 - circular_probabilities.sum()

            probabilities = np.array(
                [
                    self.fraction_recycle[ts],
                    self.fraction_remanufacture[ts],
                    self.fraction_reuse[ts],
                    landfill_probability,
                ]
            )

            # probabilities = np.array([0.0, 1.0, 0.0, 0.0])

            choices = ["recycling", "remanufacturing", "reusing", "landfilling"]
            choice = np.random.choice(choices, p=np.array(probabilities))
            return choice

    def populate_units(self, number_of_units: int = 100) -> None:
        """
        This makes an initial population of functional units in the
        model.
        """

        for _ in range(number_of_units):
            unit = Unit(
                unit_type="blade",
                state="use",
                lifespan=randint(40, 80),
                transitions_table=self.transitions_table,
                context=self,
            )
            self.units.append(unit)
            self.env.process(unit.eol(self.env))

    def log_process(self, env):
        """
        This is a SimPy process that logs the state of every unit at every
        timestep.

        Parameters
        ----------
        env: simpy.Environment
            The SimPy environment which can be used to generate timeouts.
        """
        while True:
            yield env.timeout(1)
            for unit in self.units:
                self.log_list.append(
                    {
                        "ts": env.now,
                        "unit.unit_type": unit.unit_type,
                        "unit.unit_id,": unit.unit_id,
                        "unit.state": unit.state,
                    }
                )

    def run(self) -> pd.DataFrame:
        """
        This runs the model. Note that it does not initially populate the model
        first.

        Returns
        -------
        pd.DataFrame
            The log of every unit at every timestep in the simulation.
        """
        self.env.process(self.log_process(self.env))
        self.env.run(self.max_timestep)
        return self.log_df


@dataclass
class Unit:
    """
    This models a functional unit within the discrete time model.

    Instance attributes
    -------------------
    unit_type: str
        The type of unit this is (e.g., "turbine blade")

    state: str
        The current state of the functional unit.

    lifespan: int
        The lifespan of the functional unit in discrete timesteps

    context: Context
        The context (class from above) in which the unit operates.

    transitions_table: Dict[StateTransition, NextState]
        The dictionary that controls the state transitions.

    unit_id: str
        The unique identifier for the unit. This doesn't rely on the
        type of unit. If it is not overridden, it defaults to a UUID.
    """

    unit_type: str
    state: str
    lifespan: int
    context: Context
    transitions_table: Dict[StateTransition, NextState]
    unit_id: str = field(default_factory=unique_identifer_str)

    def __str__(self):
        """
        A reasonable string representaiton of the unit for use with print().
        """
        return f"type: {self.unit_type}, id:{self.unit_id}, state: {self.state}, lifespan:{self.lifespan}"

    def transition(self, transition: str) -> None:
        """
        Transition the unit's state machine from the current state based on a
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
        self.lifespan = next_state.eol

    def eol(self, env):
        """
        This is a generator for the SimPy process that controls what happens
        when this unit reaches the end of its lifespan. The duration of the
        timeout is controlled by this lifespan.

        Parameters
        ----------
        env: simpy.Environment
            The SimPy environment controlling the lifespan of this unit.
        """
        unit_has_not_been_landfilled = True
        while unit_has_not_been_landfilled:
            yield env.timeout(self.lifespan)
            next_transition = self.context.probabilistic_transition(self, env.now)
            self.transition(next_transition)
