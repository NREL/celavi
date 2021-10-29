from typing import Deque, Tuple, Dict
from collections import deque


class Component:
    def __init__(
        self,
        context,
        kind: str,
        year: int,
        lifespan_timesteps: float,
        manuf_facility_id: int,
        in_use_facility_id: int,
        mass_tonnes: Dict[str, float] = 0,
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

        mass_tonnes: Dict[str, float]
            The masses of the materials of the component, in tonnes. Keys are
            material names. Values are material masses.

        manuf_facility_id: int
            The initial facility id (where the component begins life) used in
            initial pathway selection from CostGraph.

        in_use_facility_id: int
            The facility ID where the component spends its useful lifetime
            before beginning the end-of-life process.
        """

        self.current_location = ""  # There is no location initially
        self.context = context
        self.kind = kind
        self.year = year
        self.mass_tonnes = mass_tonnes
        self.manuf_facility_id = manuf_facility_id
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
        in_use_facility_id = f"in use_{int(from_facility_id)}"
        path_choices = self.context.cost_graph.choose_paths(source=in_use_facility_id)
        path_choices_dict = {path_choice['source']: path_choice for path_choice in path_choices}

        path_choice = path_choices_dict[in_use_facility_id]
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
        begin_timestep = (self.year - self.context.min_year) * self.context.timesteps_per_year
        yield env.timeout(begin_timestep)
        self.current_location = 'manufacturing_' + str(self.manuf_facility_id)
        lifespan = 1
        count_inventory = self.context.count_facility_inventories[self.current_location]
        mass_inventory = self.context.mass_facility_inventories[self.current_location]
        count_inventory.increment_quantity(self.kind, 1, env.now)

        for material, mass in self.mass_tonnes.items():
            mass_inventory.increment_quantity(material, mass, env.now)

        yield env.timeout(lifespan)
        # only inbound transportation is tracked
        count_inventory.increment_quantity(self.kind, -1, env.now)

        for material, mass in self.mass_tonnes.items():
            mass_inventory.increment_quantity(material, -mass, env.now)

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
            if self.current_location.startswith('manufacturing'):
                # Query cost graph
                self.create_pathway_queue(self.in_use_facility_id)

            if len(self.pathway) > 0:
                location, lifespan, distance = self.pathway.popleft()

                if 'fine grinding' in location:
                    # increment the fine grinding inventory and transpo tracker
                    fg_count_inventory = self.context.count_facility_inventories[location]
                    fg_transport = self.context.transportation_trackers[location]
                    fg_mass_inventory = self.context.mass_facility_inventories[location]
                    fg_count_inventory.increment_quantity(
                        self.kind,
                        1,
                        env.now
                    )

                    # Assuming that all materials incur the same impacts
                    # to transport. So whether you are transporting a tonne of
                    # GFRP or a ton of steel, it is the same impact. Perhaps
                    # not true?

                    for _, mass in self.mass_tonnes.items():
                        fg_transport.increment_inbound_tonne_km(mass * distance, env.now)

                    for material, mass in self.mass_tonnes.items():
                        fg_mass_inventory.increment_quantity(material, mass, env.now)

                    # locate the nearest landfill and increment for material loss
                    _loss_landfill = self.context.cost_graph.find_downstream(
                        facility_id = int(location.split('_')[1]),
                        connect_to = 'landfill'
                    )

                    lf_count_inventory = self.context.count_facility_inventories[_loss_landfill]
                    lf_transport = self.context.transportation_trackers[_loss_landfill]
                    lf_mass_inventory = self.context.mass_facility_inventories[_loss_landfill]
                    lf_count_inventory.increment_quantity(
                        self.kind,
                        self.context.cost_graph.finegrind_material_loss,
                        env.now
                    )

                    for material, mass in self.mass_tonnes.items():
                        lf_transport.increment_inbound_tonne_km(
                            self.context.cost_graph.finegrind_material_loss * mass * distance,
                            env.now
                        )
                        lf_mass_inventory.increment_quantity(
                            material,
                            self.context.cost_graph.finegrind_material_loss * mass,
                            env.now
                        )

                    # locate the nearest next use facility and increment the rest
                    _next_use = self.context.cost_graph.find_downstream(
                        node_name = location,
                        connect_to = 'next use')

                    nu_count_inventory = self.context.count_facility_inventories[_next_use]
                    nu_mass_inventory = self.context.mass_facility_inventories[_next_use]
                    nu_transport = self.context.transportation_trackers[_next_use]
                    nu_count_inventory.increment_quantity(
                        self.kind,
                        1 - self.context.cost_graph.finegrind_material_loss,
                        env.now
                    )

                    for material, mass in self.mass_tonnes.items():
                        nu_mass_inventory.increment_quantity(
                            material,
                            (1 - self.context.cost_graph.finegrind_material_loss) * mass,
                            env.now
                        )

                        nu_transport.increment_inbound_tonne_km(
                            (1 - self.context.cost_graph.finegrind_material_loss) * mass * distance,
                            env.now
                        )

                    yield env.timeout(lifespan)

                    fg_count_inventory.increment_quantity(self.kind, -1, env.now)
                    for material, mass in self.mass_tonnes.items():
                        fg_mass_inventory.increment_quantity(material, -mass, env.now)

                elif 'next use' in location:
                    # the inventory and transportation was incremented when the
                    # blade hit the fine grinding step
                    pass

                else:
                    count_inventory = self.context.count_facility_inventories[location]
                    mass_inventory = self.context.mass_facility_inventories[location]
                    transport = self.context.transportation_trackers[location]
                    count_inventory.increment_quantity(self.kind, 1, env.now)

                    for material, mass in self.mass_tonnes.items():
                        mass_inventory.increment_quantity(material, mass, env.now)

                    # Again, assuming the transportation impacts are the same per unit
                    # mass for all materials.
                    for _, mass in self.mass_tonnes.items():
                        transport.increment_inbound_tonne_km(mass * distance, env.now)

                    self.current_location = location

                    yield env.timeout(lifespan)

                    count_inventory.increment_quantity(self.kind, -1, env.now)

                    for material, mass in self.mass_tonnes.items():
                        mass_inventory.increment_quantity(material, -mass, env.now)

            else:
                break
