"""
Methods for dealing with uncertainty information on parameter values.
"""
import scipy.stats as st

def apply_array_uncertainty(quantity, run):
    """
    Use model run number to access one element in a parameter list.

    When quantity is a List, then the value of quantity with the index run is returned.
    When quantity is a Dict, the value assigned to the key "value" is returned.
    When quantity is a float, it is returned as-is.    

    Parameters
    ----------
    quantity: List, Dict, or float
        A data structure containing a range of parameter values (floats), distribution parameters, or a single float

    run: int
        The current CELAVI run number

    Returns
    -------
    A single float representing the value of quantity during run
    """
    if isinstance(quantity, list):
        return float(quantity[run])
    elif isinstance(quantity,dict):
        return float(quantity['value'])
    else:
        return float(quantity)

def apply_stoch_uncertainty(quantity, seed=1, distn=st.triang):
    """
    Draw from distribution if parameters exist.

    When quantity is a Dict, it must contain distribution parameters as well as a key named "value".
    Once a parameter value has been drawn from the distribution, it is stored under "value".
    When quantity is a float, it is returned as-is.

    distn defaults to a triangular distribution. If another distribution is used, this method
    will need to be edited to use the relevant parameters.

    Parameters
    ----------
    quantity: Dict or float
        Contains distribution parameters and a key:value pair for storing the random draw.

    seed: int or an instance of np.random.default_rng
        Defines the current random state. Must be passed in from Scenario for reproducibility.

    distn: Distribution available in scipy.stats
        Defaults to the triangular distribution.
    """
    if isinstance(quantity, dict):
        # return the parameter value drawn from a distribution
        if all([i in quantity.keys() for i in ['c', 'loc', 'scale']]):
            return distn.rvs(c=quantity['c'],
                            loc=quantity['loc'],
                            scale=quantity['scale'],
                            random_state=seed
                            )
        else:
            return quantity['value']
    else:
        # return the parameter value in the config file
        return float(quantity)
