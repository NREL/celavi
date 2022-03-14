import numpy as np


class TransportationTracker:
    """
    The TransportationTracker class inbound tonne*km values into a facility.
    What distinguishes this class from the FacilityInventory is that
    the inbound tonne_km only increments.
    """

    def __init__(self, timesteps):
        """
        Parameters
        ----------
        timesteps
            An integer of the maximum number of timesteps that will be
            recorded in the model.
        """

        self.inbound_tonne_km = np.zeros(timesteps)
        self.route_id = np.array([None] * timesteps) 

    def increment_inbound_tonne_km(self, tonne_km, route_id, timestep):
        """
        Parameters
        ----------
        tonne_km
            A float of the number of tonne*km being transported during the
            given timestep.

        timestep
            The timestep that is being incremented.
        """

        timestep = int(timestep)
        self.inbound_tonne_km[timestep] = self.inbound_tonne_km[timestep] + tonne_km
        self.route_id[timestep] = route_id
