import pandas as pd
import networkx as nx

from typing import Deque, Tuple, Dict
from collections import deque
from itertools import compress

from celavi.uncertainty_methods import apply_array_uncertainty


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
            The supply chain context that contains this component.

        kind: str
            The type of this component. It isn't called "type" because
            "type" is a keyword in Python.

        year: int
            The calendar year in which this component enters the in use state
            for the first time.

        lifespan_timesteps: float
            The component's first useful lifetime: the amount of time, in 
            DES timesteps, that the component spends in its first in use 
            state. The argument can be provided as a floating point value,
            but it is converted into an integer before it is assigned to 
            the instance attribute. This allows components to have either
            fixed integer lifespans, fixed float lifespans, or lifespans
            defined with a Weibull probability distribution.

        in_use_facility: str
            The node name where the component spends its first useful lifetime
            before beginning the end-of-life process.
        
        mass_tonnes: Dict[str, float]
            Component composition by material, in metric tonnes. Keys are
            material names. Values are material masses.            
        """

        self.context = context
        self.kind = kind
        # Note that this is NOT the current simulation year, but the year in which
        # the component first enters use.
        self.year = year
        self.mass_tonnes = mass_tonnes
        # How many components are in this component - required for material loss
        # accounting; always 1
        self.count = 1.0
        self.in_use_facility = in_use_facility
        # Manufacturing facility is assigned during component
        # beginning of life (bol_process)
        self.manuf_facility = None
        self.initial_lifespan_timesteps = int(lifespan_timesteps)  # timesteps
        # The list of EOL processes the component will visit at EOL gets
        # stored in this attribute after its first useful lifetime
        self.pathway: Deque[Tuple[str, int]] = deque()
        # Information on material losses in some processes
        self.split_dict = self.context.path_dict["path_split"]

    def create_pathway_queue(self):
        """
        Query the CostGraph instance and construct an EOL process queue for
        this component. This method is called during the eol_process when, and
        uses the component's in_use_facility (node name) attribute to select the
        starting point for the EOL process queue.

        This method does not return anything, rather it modifies the
        instance attribute self.pathway with a new deque.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        path_choices = self.context.cost_graph.choose_paths(source_node=self.in_use_facility)
        path_choices_dict = {
            path_choice["source"]: path_choice for path_choice in path_choices
        }

        path_choice = path_choices_dict[self.in_use_facility]
        self.pathway = deque()
        for facility, lifespan, distance, route_id in path_choice["path"]:
            # Overwrite the default timespan from CostGraph for the in use phase.
            if 'in use' in facility:
                self.pathway.append(
                    (facility, self.initial_lifespan_timesteps, distance, route_id)
                )
            # Also overwrite the default timespan for facilities where components
            # do not leave during the simulation.
            elif any(
                [
                    facility.startswith(i)
                    for i in self.context.path_dict["permanent_lifespan_facility"]
                ]
            ):
                self.pathway.append(
                    (facility, self.context.max_timesteps * 2, distance, route_id)
                )
            # Otherwise, use the default timespan obtained from CostGraph (1 timestep).
            else:
                self.pathway.append((facility, lifespan, distance, route_id))

    def bol_process(self, env):
        """
        This process starts the first useful lifetime for this component. Since it is
        only called once, it does not have a loop, like most other SimPy
        processes. When the component reaches end-of-life, this method
        sets the end-of-life (EOL) pathway for the component.

        Parameters
        ----------
        env: simpy.Environment
            The SimPy environment running the DES timesteps.
        
        Returns
        -------
        None
        """
        begin_timestep = (
            self.year - self.context.min_year
        ) * self.context.timesteps_per_year

        # Apart from the in use node, the component will spend only
        # "lifespan" timesteps in each node
        lifespan = 1

        # component waits to be manufactured
        yield env.timeout(begin_timestep)

        # Identify manufacturing facility based on distance and, for secondary manuf 
        # facilities, whether the facility has sufficient inventory to manufacture the
        # component
        
        # Locate the closest (by cost) manufacturing facilities
        _manuf_dict = self.context.cost_graph.find_upstream_neighbor(
            node_id = self.in_use_facility,
            crit = 'cost', # @NOTE Replace with 'dist' to look at location only, not processing costs
        )
        # Sort facilities by increasing distance criterion, then search along the list of facilities
        # until EITHER a virgin facility is found OR a secondary facility with sufficient inventory 
        # is found
        _manuf_sorted = sorted(_manuf_dict, key=_manuf_dict.get)
        # @TODO Hardcoding alert! Pass sc_begin in from scenario.yaml to remove
        # Check to see if the closest facility is a virgin manufacturing facility
        for _fac in _manuf_sorted:
            if _fac.split('_')[0] in ['window glass recovery','solar glass manufacturing from cullet']:
                # If the facility is a secondary facility, then check that the inventory is sufficient to 
                # manufacture the component
                _fac_inv_mass = self.context.mass_facility_inventories[_fac].cumulative_history
                _fac_inv_count = self.context.count_facility_inventories[_fac].cumulative_history
                if all(
                    [_fac_inv_mass.loc[_fac_inv_mass.timestep == begin_timestep][material].values[0] > mass 
                     for material, mass in self.mass_tonnes.items()]
                    ) and (_fac_inv_count.loc[_fac_inv_count.timestep == begin_timestep][self.kind].values[0] > self.count):
                    self.manuf_facility = _fac
                    # "break" ends the loop
                    break
                else:
                    # "pass" begins the next iteration of the loop
                    pass
            # If the closest facility IS a virgin manuf facility, then no need to check the inventory;
            # this component is manufactured at this facility
            else:
                self.manuf_facility = _fac          
                break
        
        # Increment manufacturing inventories
        count_inventory = self.context.count_facility_inventories[self.manuf_facility]
        mass_inventory = self.context.mass_facility_inventories[self.manuf_facility]
        # @TODO Hardcoding alert! Pull from scenario.yaml
        if self.manuf_facility.split('_')[0] in ['window glass manufacturing', 'solar glass manufacturing']:
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
        
        # Increment and decrement intermediate manufacturing facilities
        # Identify pathway from manuf_facility to in_use_facility
        for _fac in nx.astar_path(
            self.context.cost_graph.supply_chain,
            source = self.manuf_facility,
            target = self.in_use_facility)[1:-1]:

            _count = self.context.count_facility_inventories[_fac]
            _mass = self.context.mass_facility_inventories[_fac]

            _count.increment_quantity(self.kind, 1, env.now)
            for material, mass in self.mass_tonnes.items():
                _mass.increment_quantity(material, mass, env.now)
            
            yield env.timeout(lifespan)

            _count.increment_quantity(self.kind, -1, env.now)
            for material, mass in self.mass_tonnes.items():
                _mass.increment_quantity(material, -mass, env.now)


        # Component is now in use
        
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
                # @NOTE dist > 0 logic here only kicks in for co-located facilities that
                # still require transportation (ie in tiny-circfutures)
                tonne_km = mass * dist if dist > 0 else mass * 1.0,
                # @TODO route_id should now be a string pulled from the routes file - incorporate
                route_id = None,
                timestep=env.now,
            )

        # Component stays in use for its lifetime
        yield env.timeout(self.initial_lifespan_timesteps)

        # Component's next steps are determined and stored in self.pathway
        # This method looks at the in_use_facility attribute and thus takes no parameters
        self.create_pathway_queue()

        # Component is decremented from in use inventories
        self.move_component_from(env, loc=self.in_use_facility)

        # Take the current facility (the in use facility) off the to-do list
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
        
        Returns
        -------
        None
        """
        while True:
            if self.pathway:
                # Use the component's process queue (EOL pathway) to identify the
                # component's next step
                location, lifespan, distance, route_id = self.pathway.popleft()
                factype = location.split("_")[0]

                # If the next step for the component involves material losses,
                if factype in [key for key in self.split_dict]:
                    # Pull in the mass fraction lost in this step
                    _loss = apply_array_uncertainty(self.split_dict[factype]["fraction"],self.context.model_run)

                    # Move the component to the facility that involves material losses
                    self.move_component_to(
                        env, loc=location, dist=distance, route_id=route_id, amt=1.0
                    )
                    # Update the component's location
                    self.current_location = location
                    
                    # Wait until the component has spent 'lifespan' timesteps here
                    # Generally this is only 1 timestep
                    yield env.timeout(lifespan)

                    # Move the entire component OUT of the facility that involves material losses,
                    # IF the component has a next step in its pathway
                    # If there's no next step, then only move the lost component fraction
                    # out of this facility
                    if len(self.pathway) > 0:
                        self.move_component_from(env, loc=location)
                    else:
                        self.move_component_from(env, loc=location, amt = _loss)

                    # Locate the closest facility that receives material losses
                    _split_facility_1 = self.context.cost_graph.find_nearest_factype(
                        source_node = location,
                        target_factype = self.split_dict[factype]["facility_1"],
                        crit = 'dist',
                    )

                    # Move component fractions to [landfill] facility that receives material losses
                    self.move_component_to(
                        env,
                        loc = _split_facility_1[0],
                        amt = _loss,
                        dist = _split_facility_1[1],
                        route_id = _split_facility_1[2],
                    )
                    
                    # Move the rest of the component to the next facility along pathway
                    if len(self.pathway) > 0:

                        location, lifespan, distance, route_id = self.pathway.popleft()

                        self.move_component_to(
                            env,
                            loc = location,
                            dist = distance,
                            route_id = route_id,
                            amt= (1 - _loss) * 1.0
                        )

                        # Wait until the component has spent 'lifespan' timesteps here
                        yield env.timeout(lifespan)

                        # Decrement the current facility inventory
                        self.move_component_from(env,
                                                 loc = location,
                                                 amt = (1 - _loss) * 1.0)
                        
                        # Update the component's record of its materials and masses by applying
                        # the mass fraction loss
                        self.count = (1 - _loss) * self.count
                
                # If the component is currently at a facility type noted "pass" (typically
                # end-of-supply-chain facilities), do nothing b/c the component is staying
                # here (no next step)
                elif factype in self.split_dict["pass"]:
                    self.move_component_to(
                        env, loc=location, dist=distance, route_id=route_id
                    )

                    self.current_location = location
                
                # If the component is at a facility WITHOUT material losses but WITH a next
                # step, then move the entire component along the pathway
                else:
                    self.move_component_to(
                        env, loc=location, dist=distance, route_id=route_id, amt=1.0
                    )

                    self.current_location = location

                    # Wait until the component has spent 'lifespan' timesteps here
                    yield env.timeout(lifespan)

                    self.move_component_from(env, loc=location, amt=1.0)

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
        
        Returns
        -------
        None
        """
        self.context.count_facility_inventories[loc].increment_quantity(
            self.kind, amt * self.count, env.now
        )

        for _mat, _mass in self.mass_tonnes.items():
            self.context.mass_facility_inventories[loc].increment_quantity(
                _mat, amt * self.count * _mass, env.now
            )
            self.context.transportation_trackers[loc].increment_inbound_tonne_km(
                tonne_km=amt * self.count * _mass * dist, timestep=env.now, route_id=route_id
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
        
        Returns
        -------
        None
        """

        self.context.count_facility_inventories[loc].increment_quantity(
            self.kind, -amt * self.count, env.now
        )

        for _mat, _mass in self.mass_tonnes.items():
            self.context.mass_facility_inventories[loc].increment_quantity(
                _mat, -amt * self.count * _mass, env.now
            )

