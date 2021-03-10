from typing import List, Dict

from .unique_identifier import UniqueIdentifier
from .states import StateTransition, NextState


class Component:
    """
    This class models a component in the discrete event simulation (DES) model.

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
        lifespan_timesteps: float,
        mass_tonnes: float,
    ):
        """
        This takes parameters named the same as the instance variables. See
        the comments for the class for further information about instance
        attributes.

        It sets the initial state, which is an empty string. This is
        because there is no state until the component begins life, when
        the process defined in method begin_life() is called by SimPy.

        Parameters
        ----------
        context: Context
            The context that contains this component.

        kind: str
            The type of this component. The word "type", however, is also a Python
            keyword, so this attribute is named kind.

        xlong: float
            The longitude of the component.

        ylat: float
            The latitude of the component.

        year: int
            The year in which this component enters the use state for the first
            time.

        lifespan_timesteps: float
            The lifespan, in timesteps, of the component. The argument can be
            provided as a floating point value, but it is converted into an
            integer before it is assigned to the instance attribute. This allows
            more intuitive integration with random number generators defined
            outside this class which may return floating point values.

        mass_tonnes: float
            The total mass of the component, in tonnes.
        """

        self.state = ""  # There is no state until beginning of life
        self.context = context
        self.id = UniqueIdentifier.unique_identifier()
        self.kind = kind
        self.xlong = xlong
        self.ylat = ylat
        self.year = year
        self.mass_tonnes = mass_tonnes
        self.lifespan_timesteps = int(lifespan_timesteps)  # timesteps
        self.transitions_table = self.make_transitions_table()
        self.transition_list: List[str] = []

    def make_transitions_table(self) -> Dict[StateTransition, NextState]:
        """
        This method should be called once during instantiation of a component.

        It creates the table of states, transitions, and next states.

        Both recycling and landfilling have long lifetimes. For an explanation
        of why, see their state entry functions.

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
            StateTransition(state="use", transition="recycling_to_raw"): NextState(
                state="recycle_to_raw",
                lifespan_min=1000,
                lifespan_max=1000,
                state_entry_function=self.recycle_to_raw,
                state_exit_function=self.leave_use,
            ),
            StateTransition(state="use", transition="recycling_to_clinker"): NextState(
                state="recycle_to_clinker",
                lifespan_min=1000,
                lifespan_max=1000,
                state_entry_function=self.recycle_to_clinker,
                state_exit_function=self.leave_use,
            )
        }

        return transitions_table

    @staticmethod
    def recycle_to_raw(context, component, timestep: int) -> None:
        """
        Recycles a component by incrementing the material in recycling storage.

        Currently, there is no corresponding leave_recycle because only other
        processes deduct from the recycling inventory (e.g., manufacturing)

        Parameters
        ----------
        context: Context
            The context in which this component lives. There is no type
            in the method signature to prevent a circular dependency.

        component: Component
            The component which is being landfilled.

        timestep: int
            Current model timestep
        """
        _yield = context.cost_params['fine_grind_yield'] * context.cost_params['coarse_grind_yield']
        _loss = 1 - _yield

        context.recycle_to_raw_component_inventory.increment_quantity(
            item_name=component.kind, quantity=_yield, timestep=timestep
        )
        context.recycle_to_raw_material_inventory.increment_quantity(
            item_name=component.kind, quantity=_yield*component.mass_tonnes, timestep=timestep
        )
        context.landfill_component_inventory.increment_quantity(
            item_name=component.kind, quantity=_loss, timestep=timestep
        )
        context.landfill_material_inventory.increment_quantity(
            item_name=component.kind, quantity=_loss*component.mass_tonnes, timestep=timestep)

    @staticmethod
    def recycle_to_clinker(context, component, timestep:int) -> None:
        """
        Recycles a component to clinker by incrementing the material in
        recycling-to-clinker storage.

        Currently, there is no corresponding leave_recycle because only other
        processes deduct from the recycling inventory (e.g., manufacturing)

        Parameters
        ----------
        context: Context
            The context in which this component lives. There is no type
            in the method signature to prevent a circular dependency.

        component: Component
            The component which is being landfilled.

        timestep: int
            Current model timestep
        """
        _yield = context.cost_params['coarse_grind_yield']
        _loss = 1.0 - _yield
        context.recycle_to_clinker_component_inventory.increment_quantity(
            item_name=component.kind, quantity=_yield, timestep=timestep
        )
        context.recycle_to_clinker_material_inventory.increment_quantity(
            item_name=component.kind, quantity=_yield * component.mass_tonnes, timestep=timestep
        )
        context.landfill_component_inventory.increment_quantity(
            item_name=component.kind, quantity=_loss, timestep=timestep
        )
        context.landfill_material_inventory.increment_quantity(
            item_name=component.kind, quantity=_loss*component.mass_tonnes, timestep=timestep)

    @staticmethod
    def landfill(context, component, timestep:int) -> None:
        """
        Landfills a component by incrementing the material in the landfill.

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

        timestep:int
            Current model timestep
        """
        # print(f"Landfill process component {component.id}, kind {component.kind} timestep={timestep}")
        context.landfill_component_inventory.increment_quantity(
            item_name=component.kind, quantity=1, timestep=timestep,
        )
        context.landfill_material_inventory.increment_quantity(
            item_name=component.kind, quantity=component.mass_tonnes, timestep=timestep,
        )

    @staticmethod
    def use(context, component, timestep:int) -> None:
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

        timestep:int
            Current model timestep
        """
        # print(f"Use process component {component.id}, timestep={timestep}")
        context.use_component_inventory.increment_quantity(
            item_name=component.kind, quantity=1, timestep=timestep,
        )
        context.use_mass_inventory.increment_quantity(
            item_name=component.kind, quantity=component.mass_tonnes, timestep=timestep,
        )

        # This will need to be conditional on manufacturing
        context.virgin_component_inventory.increment_quantity(
            item_name=component.kind, quantity=-1, timestep=timestep
        )
        context.virgin_material_inventory.increment_quantity(
            item_name=component.kind, quantity=-component.mass_tonnes,
            timestep=timestep,
        )



    @staticmethod
    def leave_use(context, component, timestep:int):
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

        timestep: int
            Current model timestep
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
        self.lifespan_timesteps = next_state.lifespan
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
            yield env.timeout(self.lifespan_timesteps)
            next_transition = self.context.choose_transition(self, env.now)
            self.transition(next_transition, env.now)
