# TODO: Add a short module docstring above the code to:
#  1) provide authors, date of creation
#  2) give a high level description (2-3 lines) of what the module does
#  3) write any other relevant information

import numpy as np


class TransportationTracker:
    """
    The TransportationTracker class inbound tonne*km values into a facility.
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

    def increment_inbound_tonne_km(self, tonne_km, timestep):
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
