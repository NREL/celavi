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
    state: str
    transition: str


@dataclass(frozen=True)
class NextState:
    state: str
    eol_min: int = 40
    eol_max: int = 80

    @property
    def eol(self):
        return (
            self.eol_min
            if self.eol_min == self.eol_max
            else randint(self.eol_min, self.eol_max + 1)
        )


class Context:
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
                state="landfill", eol_min=1000, eol_max=1000
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
        result = pd.DataFrame(self.log_list)
        return result

    @property
    def max_timestep(self) -> int:
        return len(self.fraction_reuse)

    # Could not make a type for unit (it needs to be of type Unit) because unit is
    # defined below context.
    def probabilistic_transition(self, unit, ts: int) -> str:
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

    def log_process(self, env) -> None:
        while True:
            yield env.timeout(1)
            for unit in self.units:
                self.log_list.append(
                    {
                        "ts": env.now,
                        "unit.unit_type": unit.unit_type,
                        "unit.unit_id,": unit.unit_id,
                        "unit.lifespan": unit.lifespan,
                        "unit.state": unit.state,
                    }
                )

    def run(self) -> pd.DataFrame:
        self.env.process(self.log_process(self.env))
        self.env.run(self.max_timestep)

        return self.log_df


@dataclass
class Unit:
    unit_type: str
    state: str
    lifespan: int
    context: Context
    transitions_table: Dict[StateTransition, NextState]
    unit_id: str = field(default_factory=unique_identifer_str)

    def __str__(self):
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

    def eol(self, env) -> None:
        unit_has_not_been_landfilled = True
        while unit_has_not_been_landfilled:
            yield env.timeout(self.lifespan)
            next_transition = self.context.probabilistic_transition(self, env.now)
            self.transition(next_transition)
