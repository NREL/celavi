from typing import Deque, Tuple, Dict
from collections import deque

from celavi.scenario import apply_array_uncertainty


class Component:
    """
    The Component class works with the Context class to run the discrete
    event simulation. There is one instance of Component per physical
    component in the simulation. This class models each step in the
    lifecycle of the component, from begining of life (BOL) to end of
    life (EOL).
    """

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
            The type of this component. It isn't called "type" because
            "type" is a keyword in Python.

        year: int
            The calendar year in which this component enters the in use state
            for the first time.

        lifespan_timesteps: float
            The component useful lifetime: the period, in timesteps, that
            the component spends in its first in use state. The argument
            can be provided as a floating point value, but it is converted
            into an integer before it is assigned to the instance attribute.
            This allows components to have either fixed integer lifespans,
            fixed float lifespans, or lifespans defined with a Weibull 
            probability distribution.

        mass_tonnes: Dict[str, float]
            Component composition by material, in tonnes. Keys are
            material names. Values are material masses.

        manuf_facility_id: int
            The facility id where the component begins life (typically but not
            necessarily a manufacturing facility type) used in initial pathway
            selection from CostGraph.

        in_use_facility_id: int
            The facility ID where the component spends its first useful lifetime
            before beginning the end-of-life process (typically but not necessarily
            a renewable energy power plant).
        """

        self.context = context
        self.kind = kind
        self.year = year
        self.mass_tonnes = mass_tonnes
        self.manuf_facility_id = manuf_facility_id
        self.in_use_facility_id = in_use_facility_id
        self.current_location = "manufacturing_" + str(self.manuf_facility_id)
        self.initial_lifespan_timesteps = int(lifespan_timesteps)  # timesteps
        self.pathway: Deque[Tuple[str, int]] = deque()
        self.split_dict = self.context.path_dict["path_split"]

    def create_pathway_queue(self, from_facility_id: int):
        """
        Query the CostGraph instance and construct a queue of the lifecycle for
        this component. This method is called during the manufacturing step
        and during the eol_process when exiting the in use stage.

        This method does not return anything, rather it modifies the
        instance attribute self.pathway with a new deque.

        Parameters
        ----------
        from_facility_id: int
            The starting location of the the component.
        """
        in_use_facility_id = f"in use_{int(from_facility_id)}"
        path_choices = self.context.cost_graph.choose_paths(source=in_use_facility_id)
        path_choices_dict = {
            path_choice["source"]: path_choice for path_choice in path_choices
        }

        path_choice = path_choices_dict[in_use_facility_id]
        self.pathway = deque()
        for facility, lifespan, distance, route_id in path_choice["path"]:
            # Override the initial timespan when component goes into use.

            if facility.startswith("in use"):
                self.pathway.append(
                    (facility, self.initial_lifespan_timesteps, distance, route_id)
                )
            elif any(
                [
                    facility.startswith(i)
                    for i in self.context.path_dict["permanent_lifespan_facility"]
                ]
            ):
                self.pathway.append(
                    (facility, self.context.max_timesteps * 2, distance, route_id)
                )
            # Otherwise, use the timespan the model gives us.
            else:
                self.pathway.append((facility, lifespan, distance, route_id))

    def bol_process(self, env):
        """
        This process starts the lifecycle for this component. Since it is
        only called once, it does not have a loop, like most other SimPy
        processes. When the component reaches end-of-life, this method
        sets the end-of-life (EOL) pathway for the component.

        Parameters
        ----------
        env: simpy.Environment
            The SimPy environment running the DES timesteps.
        """
        begin_timestep = (
            self.year - self.context.min_year
        ) * self.context.timesteps_per_year
        lifespan = 1

        # component waits to be manufactured
        yield env.timeout(begin_timestep)

        # Increment manufacturing inventories
        count_inventory = self.context.count_facility_inventories[self.current_location]
        mass_inventory = self.context.mass_facility_inventories[self.current_location]
        count_inventory.increment_quantity(self.kind, 1, env.now)
        for material, mass in self.mass_tonnes.items():
            mass_inventory.increment_quantity(material, mass, env.now)

        # Component waits to transition to in use
        yield env.timeout(lifespan)

        # Decrement manufacturing inventories
        # No transportation here: transportation is tracked at destination
        # facilities
        count_inventory.increment_quantity(self.kind, -1, env.now)
        for material, mass in self.mass_tonnes.items():
            mass_inventory.increment_quantity(material, -mass, env.now)

        # Component is now in use; update the location
        self.current_location = f"in use_{int(self.in_use_facility_id)}"

        # Increment in use inventories
        count_inventory = self.context.count_facility_inventories[self.current_location]
        mass_inventory = self.context.mass_facility_inventories[self.current_location]
        count_inventory.increment_quantity(self.kind, 1, env.now)
        for material, mass in self.mass_tonnes.items():
            mass_inventory.increment_quantity(material, mass, env.now)

        # Increment transportation to in use facilities
        count_transport = self.context.transportation_trackers[self.current_location]
        for _, mass in self.mass_tonnes.items():
            count_transport.increment_inbound_tonne_km(
                tonne_km=mass
                * self.context.cost_graph.supply_chain.edges[
                    f"manufacturing_{int(self.manuf_facility_id)}",
                    f"in use_{int(self.in_use_facility_id)}",
                ]["dist"],
                route_id=self.context.cost_graph.supply_chain.edges[
                    f"manufacturing_{int(self.manuf_facility_id)}",
                    f"in use_{int(self.in_use_facility_id)}",
                ]["route_id"],
                timestep=env.now,
            )

        # Component stays in use for its lifetime
        yield env.timeout(self.initial_lifespan_timesteps)

        # Component's next steps are determined and stored in self.pathway
        self.create_pathway_queue(self.in_use_facility_id)

        # Component is decremented from in use inventories
        count_inventory.increment_quantity(self.kind, -1, env.now)
        for material, mass in self.mass_tonnes.items():
            mass_inventory.increment_quantity(material, -mass, env.now)
        # Take the current facility off the to-do list
        self.pathway.popleft()

        # Begin the end of life process
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
            if self.pathway:
                location, lifespan, distance, route_id = self.pathway.popleft()
                factype = location.split("_")[0]
                if factype in self.split_dict.keys():
                    # increment the facility inventory and transportation tracker
                    self.move_component_to(
                        env, loc=location, dist=distance, route_id=route_id
                    )
                    self.current_location = location

                    yield env.timeout(lifespan)

                    self.move_component_from(env, loc=location)

                    # locate the two downstream facilities that are closest
                    _split_facility_1 = self.context.cost_graph.find_downstream(
                        facility_id=int(location.split("_")[1]),
                        connect_to=self.split_dict[factype]["facility_1"],
                        get_dist=True,
                    )

                    _split_facility_2 = self.context.cost_graph.find_downstream(
                        node_name=location,
                        connect_to=self.split_dict[factype]["facility_2"],
                        get_dist=True,
                    )

                    # Move component fractions to the split facilities
                    self.move_component_to(
                        env,
                        loc=_split_facility_1[0],
                        amt=apply_array_uncertainty(
                            self.split_dict[factype]["fraction"],
                            self.context.model_run
                            ),
                        dist=_split_facility_1[1],
                        route_id=_split_facility_1[2],
                    )
                    self.move_component_to(
                        env,
                        loc=_split_facility_2[0],
                        amt=1 - apply_array_uncertainty(
                            self.split_dict[factype]["fraction"],
                            self.context.model_run
                            ),
                        dist=_split_facility_2[1],
                        route_id=_split_facility_2[2],
                    )
                elif factype in self.split_dict["pass"]:
                    pass

                else:
                    self.move_component_to(
                        env, loc=location, dist=distance, route_id=route_id
                    )

                    self.current_location = location

                    yield env.timeout(lifespan)

                    self.move_component_from(env, loc=location)

            else:
                break

    def move_component_to(self, env, loc, dist: float, route_id=None, amt=1.0):
        """
        Increment mass, count, and transportation inventories.

        Parameters
        ----------
        env: simpy.Environment
            The environment in which this process is running.
        
        loc: int
            Destination facility ID.
        
        dist : float
            Transportation distance in km to destination facility.
        
        route_id : str
            UUID for route along which component is moved. Defaults to None.

        amt : float
            Number of components being moved. Defaults to 1.        
        """
        self.context.count_facility_inventories[loc].increment_quantity(
            self.kind, amt, env.now
        )

        for _mat, _mass in self.mass_tonnes.items():
            self.context.mass_facility_inventories[loc].increment_quantity(
                _mat, amt * _mass, env.now
            )
            self.context.transportation_trackers[loc].increment_inbound_tonne_km(
                tonne_km=amt * _mass * dist, timestep=env.now, route_id=route_id
            )

    def move_component_from(self, env, loc, amt=1.0):
        """
        Decrement mass and count inventories at the current facility.

        Only INBOUND transportation is tracked, thus no transportation
        tracking is done by this method.

        Parameters
        ----------
        env: simpy.Environment
            The environment in which this process is running.

        loc: int
            Current facility ID.
        
        amt : float
            Number of components being moved. Defaults to 1.
        """

        self.context.count_facility_inventories[loc].increment_quantity(
            self.kind, -amt, env.now
        )

        for _mat, _mass in self.mass_tonnes.items():
            self.context.mass_facility_inventories[loc].increment_quantity(
                _mat, -amt * _mass, env.now
            )

