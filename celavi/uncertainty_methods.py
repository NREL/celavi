import scipy.stats as st

def apply_array_uncertainty(quantity, run):
    """Use model run number to access one element in a parameter list."""
    if isinstance(quantity, list):
        return float(quantity[run])
    elif isinstance(quantity,dict):
        return float(quantity['value'])
    else:
        return float(quantity)

def apply_stoch_uncertainty(quantity, seed=1, distn=st.triang):
    """Draw from distribution if parameters exist."""
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
