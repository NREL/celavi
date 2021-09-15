from typing import Deque, Tuple
from collections import deque


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
        year: int,
        lifespan_timesteps: float,
        in_use_facility_id: int,
        mass_tonnes: float = 0,
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

        year: int
            The year in which this component enters the use state for the first
            time.

        lifespan_timesteps: float
            The lifespan, in timesteps, of the component during its first
            In use phase. The argument can be
            provided as a floating point value, but it is converted into an
            integer before it is assigned to the instance attribute. This allows
            more intuitive integration with random number generators defined
            outside this class which may return floating point values.

        mass_tonnes: float
            The total mass of the component, in tonnes. Can be None if the component
            mass is not being used.

        in_use_facility_id: int
            The initial facility id (where the component begins life) used in
            initial pathway selection from CostGraph.
        """

        self.current_location = ""  # There is no location initially
        self.context = context
        self.kind = kind
        self.year = year
        self.mass_tonnes = mass_tonnes
        self.in_use_facility_id = in_use_facility_id
        self.initial_lifespan_timesteps = int(lifespan_timesteps)  # timesteps
        self.pathway: Deque[Tuple[str, int]] = deque()

    def create_pathway_queue(self, from_facility_id: int):
        """
        Query the CostGraph and construct a queue of the lifecycle for
        this component. This method is called during the manufacturing step
        and during the eol_process when exiting an "in use" location.

        This method does not return anything, rather it modifies the
        instance attribute self.pathway with a new deque.

        Parameters
        ----------
        from_facility_id: int
            The starting location of the the component.
        """
        path_choices = self.context.cost_graph.choose_paths()
        path_choices_dict = {path_choice['source']: path_choice for path_choice in path_choices}
        manufacturing_facility_id = f"manufacturing_{int(from_facility_id)}"
        path_choice = path_choices_dict[manufacturing_facility_id]
        self.pathway = deque()

        for facility, lifespan, distance in path_choice['path']:
            # Override the initial timespan when component goes into use.
            if facility.startswith("in use"):
                self.pathway.append((facility, self.initial_lifespan_timesteps, distance))
            # Set landfill timespan long enough to be permanent
            elif facility.startswith("landfill"):
                self.pathway.append((facility, self.context.max_timesteps * 2, distance))
            # Also set the next use facility timespan to permanent
            elif facility.startswith("next use"):
                self.pathway.append((facility, self.context.max_timesteps * 2, distance))
            # Otherwise, use the timespan the model gives us.
            else:
                self.pathway.append((facility, lifespan, distance))

    def manufacturing(self, env):
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
        begin_timestep = (self.year - self.context.min_year) / self.context.years_per_timestep
        yield env.timeout(begin_timestep)
        self.create_pathway_queue(self.in_use_facility_id)
        env.process(self.eol_process(env))

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
            if len(self.pathway) > 0:
                if self.current_location.startswith('manufacturing'):
                    # Query cost graph again
                    self.create_pathway_queue(self.in_use_facility_id)
                    # Because the blade was just manufactured, skip the first
                    # manufacturing step so that the blade is not manufactured twice in
                    # a row.
                    self.pathway.popleft()

                location, lifespan, distance = self.pathway.popleft()

                if 'fine grinding' in location:
                    # increment the fine grinding inventory and transpo tracker
                    count_inventory = self.context.count_facility_inventories[location]
                    transport = self.context.transportation_trackers[location]
                    count_inventory.increment_quantity(
                        self.kind,
                        1,
                        env.now
                    )
                    transport.increment_inbound_tonne_km(
                        self.mass_tonnes * distance,
                        env.now
                    )

                    # locate the nearest landfill and increment for material loss
                    _loss_landfill = self.context.cost_graph.find_downstream(
                        facility_id = int(location.split('_')[1]),
                        connect_to = 'landfill'
                    )

                    count_inventory = self.context.count_facility_inventories[_loss_landfill]
                    transport = self.context.transportation_trackers[_loss_landfill]
                    count_inventory.increment_quantity(
                        self.kind,
                        self.context.cost_graph.finegrind_material_loss,
                        env.now
                    )
                    transport.increment_inbound_tonne_km(
                        self.context.cost_graph.finegrind_material_loss * self.mass_tonnes * distance,
                        env.now
                    )

                    # locate the nearest next use facility and increment the rest
                    _next_use = self.context.cost_graph.find_downstream(
                        node_name = location,
                        connect_to = 'next use')

                    count_inventory = self.context.count_facility_inventories[_next_use]
                    transport = self.context.transportation_trackers[_next_use]
                    count_inventory.increment_quantity(
                        self.kind,
                        1 - self.context.cost_graph.finegrind_material_loss,
                        env.now
                    )
                    transport.increment_inbound_tonne_km(
                        (1 - self.context.cost_graph.finegrind_material_loss) * self.mass_tonnes * distance,
                        env.now
                    )
                elif 'next use' in location:
                    # the inventory and transportation was incremented when the
                    # blade hit the fine grinding step
                    pass
                else:
                    count_inventory = self.context.count_facility_inventories[location]
                    transport = self.context.transportation_trackers[location]
                    count_inventory.increment_quantity(self.kind, 1, env.now)
                    transport.increment_inbound_tonne_km(self.context.cost_graph.finegrind_material_loss * self.mass_tonnes * distance, env.now)

                self.current_location = location
                yield env.timeout(lifespan)
            else:
                break
