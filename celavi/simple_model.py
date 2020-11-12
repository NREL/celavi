from typing import Dict, List, Callable

import simpy
import pandas as pd

from .unique_identifier import UniqueIdentifier
from .states import StateTransition, NextState
from .inventory import Inventory


class Component:
    """
    This class models a component in the discrete event simulation (DES) model.

    This class defines the following instnace attributes:

    context: Context
        The context that contains this component.

    kind: str
        The type of this component. The word "type", however, is also a Python
        keyword, so this attribute is named kind.

    xlong: float
        The longitude of the component.

    xlat: float
        The latitude of the component.

    year: int
        The year in which this component enters the use state for the first
        time.

    lifespan: int
        The lifespan, in timesteps, of the component.

    mass_tonnes: float
        The total mass of the component, in tonnes.

    transitions_table: Dict[StateTransition, NextState]
        The transition table for the state machine. E.g., when a component
        begins life, it enters the "use" state. When a component is in the
        "use" state, it can receive the transition "landfilling", which
        transitions the component into the "landfill" state.
    """

    def __init__(
        self,
        context,
        kind: str,
        xlong: float,
        ylat: float,
        year: int,
        lifespan: int,
        mass_tonnes: float,
    ):
        """
        This takes parameters named the same as the instance variables. See
        the comments for the class for further information about instance
        attributes.

        It sets the initial state, which is an empty string. This is
        because there is no state until the component begins life, when
        the process defined in method begin_life() is called by SimPy.


        """

        self.state = ""  # There is no state until beginning of life
        self.context = context
        self.id = UniqueIdentifier.unique_identifier()
        self.kind = kind
        self.xlong = xlong
        self.ylat = ylat
        self.year = year
        self.mass_tonnes = mass_tonnes
        self.lifespan = lifespan  # timesteps
        self.transitions_table = self.make_transitions_table()
        self.transition_list: List[str] = []

    def make_transitions_table(self) -> Dict[StateTransition, NextState]:
        """
        This method should be called once during instantiation of a component.

        It creates the table of states, transitions, and next states.

        Returns
        -------
        Dict[StateTransition, NextState]
            A dictionary mapping current states and transitions (the key) into
            the next state (the value). See the documentation for the
            StateTransition and NextState classes.
        """
        transitions_table = {
            StateTransition(state="use", transition="landfilling"): NextState(
                state="landfill",
                lifespan_min=1000,
                lifespan_max=1000,
                state_entry_function=self.landfill,
                state_exit_function=self.leave_use,
            ),
        }

        return transitions_table

    def transition(self, transition: str, timestep: int) -> None:
        """
        This method changes the state of the component's state machine
        according to the transition parameter. If the transition is not
        allowed from the current state (for example, a "using" transition
        from a "landfill" state), this method raises a KeyError.

        This method calls the state entry and exit functions for the
        for the next and prior states. These functions perform any necessary
        computations for each transition (such as updating a landfill
        inventory).

        This method also keeps a list of transitions in the
        self.transition_list attribute.
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

    @staticmethod
    def landfill(context, component, timestep: int) -> None:
        """
        Landfills a component material by incrementing the material in the
        landfill.

        The landfill process is special because there is no corresponding
        leave_landfill method since component materials never leave the
        landfill.

        This is a static method so it can be called by an arbitrary function
        during a SimPy process. Since it is a static method, it is not
        attached to any instance of the Component class, so the component
        must be passed explicitly.

        Parameters
        ----------
        context: Context
            The context in which this component lives. There is no type
            in the method signature to prevent a circular dependency.

        component: Component
            The component which is being landfilled.
        """
        # print(f"Landfill process component {component.id}, kind {component.kind} timestep={timestep}")
        context.landfill_component_inventory.increment_quantity(
            item_name=component.kind, quantity=1, timestep=timestep,
        )
        context.landfill_mass_inventory.increment_quantity(
            item_name=component.kind, quantity=component.mass_tonnes, timestep=timestep,
        )

    @staticmethod
    def use(context, component, timestep: int) -> None:
        """
        Makes a material enter the use phases from another state.

        This is a static method so it can be called by an arbitrary function
        during a SimPy process. Since it is a static method, it is not
        attached to any instance of the Component class, so the component
        must be passed explicitly.

        Parameters
        ----------
        context: Context
            The context in which this component lives. There is no type
            in the method signature to prevent a circular dependency.

        component: Component
            The component which is being landfilled.
        """
        # print(f"Use process component {component.id}, timestep={timestep}")
        context.use_component_inventory.increment_quantity(
            item_name=component.kind, quantity=1, timestep=timestep,
        )
        context.use_mass_inventory.increment_quantity(
            item_name=component.kind, quantity=component.mass_tonnes, timestep=timestep,
        )

    @staticmethod
    def leave_use(context, component, timestep: int):
        """
        This method decrements the use inventory when a component material leaves use.

        This is a static method so it can be called by an arbitrary function
        during a SimPy process. Since it is a static method, it is not
        attached to any instance of the Component class, so the component
        must be passed explicitly.

        Parameters
        ----------
        context: Context
            The conext in which this component lives

        component: Component
            The component which is being taken out of use.
        """
        # print(
        #     f"Leave use process component_material {component.id}, timestep={timestep}"
        # )
        context.use_component_inventory.increment_quantity(
            item_name=component.kind, quantity=-1, timestep=timestep,
        )
        context.use_mass_inventory.increment_quantity(
            item_name=component.kind, quantity=-component.mass_tonnes, timestep=timestep,
        )

    def begin_life(self, env):
        """
        This process should be called exactly once during the discrete event
        simulation. It is what starts the lifetime this component. Since it is
        only called once, it does not have a loop, like most other SimPy
        processes. When the component enters life, this method immediately
        sets the end-of-life (EOL) process for the use state.

        Parameters
        ----------
        env: simpy.Environment
            The SimPy environment running the DES timesteps.
        """
        begin_timestep = (
            self.year - self.context.min_year
        ) / self.context.years_per_timestep
        yield env.timeout(begin_timestep)
        # print(
        #     f"yr: {self.year}, ts: {begin_timestep}. {self.kind} {self.id} beginning life."
        # )
        self.state = "use"
        self.transition_list.append("using")
        self.use(self.context, self, env.now)
        env.process(self.eol_process(env))

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
        This process controls the state transitions for the component at
        each end-of-life (EOL) event.

        Parameters
        ----------
        env: simpy.Environment
            The environment in which this process is running.
        """
        while True:
            yield env.timeout(self.lifespan)
            next_transition = self.context.choose_transition(self, env.now)
            self.transition(next_transition, env.now)


class Context:
    """
    The Context class:

    - Provides the discrete time sequence for the model
    - Holds all the components in the model
    - Links the SD model to the DES model
    - Provides translation of years to timesteps and back again
    """

    def __init__(
        self,
        min_year: int = 1980,
        max_timesteps: int = 272,
        years_per_timestep: float = 0.25,
    ):
        """
        Parameters
        ----------
        min_year: int
            The starting year of the model.

        max_timesteps: int
            The maximum number of discrete timesteps in the model.

        years_per_timestep: float
            The number of years covered by each timestep. Fractional
            values are allowed for timesteps that have a duration of
            less than one year.
        """

        self.max_timesteps = max_timesteps
        self.min_year = min_year
        self.years_per_timestep = years_per_timestep
        self.components: List[Component] = []
        self.env = simpy.Environment()

        self.landfill_component_inventory = Inventory(
            name="components in landfill",
            possible_items=["nacelle", "blade", "tower", "foundation",],
            timesteps=self.max_timesteps,
            quantity_unit="unit",
            can_be_negative=False,
        )

        self.use_component_inventory = Inventory(
            name="components in use",
            possible_items=["nacelle", "blade", "tower", "foundation",],
            timesteps=self.max_timesteps,
            quantity_unit="unit",
            can_be_negative=False,
        )

        self.landfill_mass_inventory = Inventory(
            name="mass in landfill",
            possible_items=["nacelle", "blade", "tower", "foundation", ],
            timesteps=self.max_timesteps,
            quantity_unit="tonne",
            can_be_negative=False,
        )

        self.use_mass_inventory = Inventory(
            name="mass in use",
            possible_items=["nacelle", "blade", "tower", "foundation", ],
            timesteps=self.max_timesteps,
            quantity_unit="tonne",
            can_be_negative=False,
        )

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

        xlong: float
            The longitude of the component.

        xlat: float
            The latitude of the component.

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
                xlong=row["xlong"],
                ylat=row["ylat"],
                year=row["year"],
                mass_tonnes=row["mass_tonnes"],
                context=self,
                lifespan=lifespan_fns[row["kind"]](),
            )
            self.env.process(component.begin_life(self.env))
            self.components.append(component)

    def choose_transition(self, component, timestep: int) -> str:
        """
        This chooses the transition (pathway) for a component when it reaches
        end of life. Currently, this only models the linear pathway where
        components are landfilled at the end of life

        The timestep of the discrete sequence is used to query the SD model
        for the current costs of each pathway as given from the learning
        by doing model.

        Parameters
        ----------
        component: Component
            The component for which a pathway is being chosen.

        timestep: int
            The timestep at which the pathway is being chosen.

        Returns
        -------
        str
            The name of the transition to make. This is then passed to
            the state machine in the component to move into the next
            state as chosen here.
        """
        if component.state == "use":
            return "landfilling"
        else:
            raise ValueError("Components must always be in the state use.")

    def run(self):
        """
        This method starts the discrete event simulation running.
        """
        self.env.run(until=int(self.max_timesteps))
        return self.landfill_component_inventory.cumulative_history, self.landfill_mass_inventory.cumulative_history
