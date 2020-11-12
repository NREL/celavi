import pysd

def get_model(pysdfile):
    """
    Imports pySD model from specified filename if it exists
    :key PySD file name (extension should be .py)
    :return pySD model
    """

    try:
        _out = pysd.load(pysdfile)
    except (FileNotFoundError, IOError):
        print('model file does not exist or cannot be read')
        _out = None

    return _out


def first_step(pysdmodel, init_time, timestep, param_dict=None, **kwargs):
    """
    - Runs an already-created PySD model for the first time step if init_time is
    set to the model start time, otherwise runs from the model start time up to
    init_time + timestep
    - Creates a .csv file where results are stored
    @note this function does not *need* to return the results
    :returns the results data frame for the first time step and the model time
    """

    if param_dict is not None:
        # run the model with user-provided parameter values
        # (may include scenario name)
        _res = pysdmodel.run(initial_condition='original',
                             params=param_dict,
                             return_timestamps=init_time)

    else:
        # run the model with a generic scenario name
        _res = pysdmodel.run(initial_condition='original',
                             params={'scenario_name': 'stepwise'},
                             return_timestamps=init_time)

    _time = init_time + timestep

    return _res, _time


def step(pysdmodel, time, timestep, param_dict=None, **kwargs):
    """
    - Runs an already-created pySD model for any single time step past the first
    - Updates the .csv file with results
    - Scenario name is defined in the first time step run
    :key
    :return the results data frame for that time step and the model time
    """

    if param_dict is not None:
        _step_res = pysdmodel.run(initial_condition='current',
                                  params=param_dict,
                                  return_timestamps=time)
    else:
        _step_res = pysdmodel.run(initial_condition='current',
                                  return_timestamps=time)

    _current_time = time + timestep

    return _step_res, _current_time


def reset_model(pysdmodel, pysdfile):
    """

    :key
    :return Nothing
    """

    del globals()[pysdmodel]

    try:
        _out = pysd.load(pysdfile)
    except (FileNotFoundError, IOError):
        print('model file does not exist or cannot be read')
        _out = None

    return _out
