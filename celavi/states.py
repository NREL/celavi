from dataclasses import dataclass
from typing import Optional, Callable
from numpy.random import randint


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
