import pandas as pd

class TransportationTracker:
    """
    The TransportationTracker class inbound tonne*km values into a facility.
    What distinguishes this class from the FacilityInventory is that
    the inbound tonne_km only increments.
    """

    def __init__(self):
        """
        Parameters
        ----------
        timesteps
            An integer of the maximum number of timesteps that will be
            recorded in the model.
        """
        self.record = pd.DataFrame(
            {'timesteps': [],
             'inbound_tonne_km': [],
             'route_id': []}
        )

    def increment_inbound_tonne_km(self, tonne_km, timestep, route_id = None):
        """
        Parameters
        ----------
        tonne_km
            A float of the number of tonne*km being transported during the
            given timestep.

        timestep
            The timestep that is being incremented.
        
        route_id : str or List[str], Default = None
            One or more route_ids along which material is transported, or None
        """
        if isinstance(route_id, list):
            _add_record = {'timesteps': [int(timestep) for r in route_id if r != 'colocated'],
                           'inbound_tonne_km': [tonne_km for r in route_id if r != 'colocated'],
                           'route_id': [r for r in route_id if r != 'colocated']}
            
        elif isinstance(route_id, str):
            if route_id == 'colocated': tonne_km = 0
            _add_record = {'timesteps': int(timestep),
                           'inbound_tonne_km': tonne_km,
                           'route_id': route_id}
        
        else:
            print(f'TransportationTracker: route_id is unexpected format: {route_id=}',flush=True)
            _add_record = {}
        
        # Add row(s) of inbound transportation
        try:
            self.record = pd.concat([self.record, pd.DataFrame(_add_record)], ignore_index=True)
        except ValueError:
            self.record = pd.concat([self.record, pd.DataFrame(_add_record, index=[0])], ignore_index=True)
        

