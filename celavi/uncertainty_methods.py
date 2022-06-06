def apply_array_uncertainty(quantity, run):
    """Use model run number to access one element in a parameter list."""
    if not isinstance(quantity, list):
        return float(quantity)
    else:
        return float(quantity[run])