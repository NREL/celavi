import pandas as pd
import networkx as nx

from typing import Deque, Tuple, Dict
from collections import deque

from celavi.uncertainty_methods import apply_array_uncertainty

import pdb
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
        manuf_facility: str,
        in_use_facility: str,
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

        manuf_facility: str
            The node name where the component begins life (typically but not
            necessarily a manufacturing facility type) used in initial pathway
            selection from CostGraph.

        in_use_facility: str
            The node name where the component spends its first useful lifetime
            before beginning the end-of-life process (typically but not necessarily
            a renewable energy power plant).
        
        mass_tonnes: Dict[str, float]
            Component composition by material, in tonnes. Keys are
            material names. Values are material masses.            
        """

        self.context = context
        self.kind = kind
        self.year = year
        self.mass_tonnes = mass_tonnes
        self.manuf_facility = manuf_facility
        self.in_use_facility = in_use_facility
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
        path_choices = self.context.cost_graph.choose_paths(source_node=self.in_use_facility)
        path_choices_dict = {
            path_choice["source"]: path_choice for path_choice in path_choices
        }

        path_choice = path_choices_dict[self.in_use_facility]
        self.pathway = deque()
        for facility, lifespan, distance, route_id in path_choice["path"]:
            # Override the initial timespan when component goes into use.

            if 'in use' in facility:
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
        count_inventory = self.context.count_facility_inventories[self.manuf_facility]
        mass_inventory = self.context.mass_facility_inventories[self.manuf_facility]
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

        
        # Increment in use inventories
        count_inventory = self.context.count_facility_inventories[self.in_use_facility]
        mass_inventory = self.context.mass_facility_inventories[self.in_use_facility]
        count_inventory.increment_quantity(self.kind, 1, env.now)
        for material, mass in self.mass_tonnes.items():
            mass_inventory.increment_quantity(material, mass, env.now)

        # Increment transportation to in use facilities
        count_transport = self.context.transportation_trackers[self.in_use_facility]
        for _, mass in self.mass_tonnes.items():
            dist = nx.astar_path_length(
                self.context.cost_graph.supply_chain,
                source = self.manuf_facility,
                target = self.in_use_facility,
                weight = 'dist'
            )
            
            count_transport.increment_inbound_tonne_km(
                # @NOTE dist > 0 logic here only kicks in for artificially small datasets with all 
                # facilities colocated ie tiny-circfutures
                tonne_km = mass * dist if dist > 0 else mass * 1.0,
                # @NOTE route_id may become a list of route_ids or may be removed altogether(?)
                route_id = None,
                timestep=env.now,
            )

        # Component stays in use for its lifetime
        yield env.timeout(self.initial_lifespan_timesteps)

        # Component's next steps are determined and stored in self.pathway
        self.create_pathway_queue(self.in_use_facility)

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
                # Update the component's process queue (EOL pathway) to remove the current
                # location etc.
                location, lifespan, distance, route_id = self.pathway.popleft()
                factype = location.split("_")[0]

                # If the component is now at a facility type that incurs material losses,
                if factype in [key for key in self.split_dict]:
                    # increment the facility inventory and transportation tracker
                    self.move_component_to(
                        env, loc=location, dist=distance, route_id=route_id
                    )
                    self.current_location = location
                    
                    # Wait until the component has spent 'lifespan' timesteps here
                    yield env.timeout(lifespan)

                    # Decrement the current facility inventory
                    self.move_component_from(env, loc=location)

                    # Locate the closest facility that receives material losses
                    _split_facility_1 = self.context.cost_graph.find_nearest_factype(
                        source_node = location,
                        target_factype = self.split_dict[factype]["facility_1"],
                        crit = 'dist',
                    )

                    # Move component fractions to [landfill] facility that receives material losses
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

                    # Move the rest of the component to the next facility along pathway
                    self.move_component_to(
                        env,
                        loc=self.pathway[0][0],
                        amt=1 - apply_array_uncertainty(
                            self.split_dict[factype]["fraction"],
                            self.context.model_run
                            ),
                        dist=self.pathway[0][2],
                        route_id=self.pathway[0][3],
                    )
                # If the component is currently at a facility type noted "pass" (typically
                # end-of-supply-chain facilities), do nothing b/c the component is staying
                # here (no next step)
                elif factype in self.split_dict["pass"]:
                    pass
                
                # If the component is at a facility WITHOUT material losses but WITH a next
                # step, then move the entire component along the pathway
                else:
                    self.move_component_to(
                        env, loc=location, dist=distance, route_id=route_id
                    )

                    self.current_location = location

                    # Wait until the component has spent 'lifespan' timesteps here
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

