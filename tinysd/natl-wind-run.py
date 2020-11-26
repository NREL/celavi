import os
import shutil
import pysd
import matplotlib.pyplot as plt
import numpy as np
from stepwise import get_model, first_step, step, reset_model

vensimdir = os.getcwd() + "\\tinysd\\"
pysdfile = 'natl-wind-importable.py'

os.chdir(vensimdir)

# if there's no pre-imported python file in this directory, convert an updated
# model located in vensimdir and move it to this directory
# otherwise, load the pysd model in pysdfile
if pysdfile in os.listdir():
    model = pysd.load(pysdfile)
else:
    print('creating new .py file from .mdl')
    # create a .py file from .mdl file
    model = pysd.read_vensim(vensimdir + "natl-wind-importable.mdl")
    # move new .py file to this file's directory (unnecessary?)
    shutil.move(vensimdir + "natl-wind-importable.py", os.getcwd())

# Instructions on editing a fresh pysd import to avoid various errors
## AFTER NEW IMPORT FROM MDL, edit pysd model
# Manual at the moment
# @todo automate this process

# Add import statement
# from pandas import read_csv

# Replace externalities_total() function definition with the following:
# _out = np.nan
#
# if annual_demand() == 0:
#     _out = 0
# else:
#     _out = (
#                        externalities_from_reusing() + externalities_from_remanufacturing() +
#                        externalities_from_recycling() + externalities_from_extracting() +
#                        externalities_from_total_transportation()) / annual_demand()
#
# return _out

# Replace unit_externalities_from_recycling() function definition with the following:
# _out = np.nan
#
# if annual_demand() == 0:
#     _out = 0
# else:
#     _out = externalities_from_recycling() / annual_demand()
#
# return _out

# Replace unit_externalities_from_remanufacturing() function definition with the following:
# _out = np.nan
#
# if annual_demand() == 0:
#     _out = 0
# else:
#     _out = externalities_from_remanufacturing() / annual_demand()
#
# return _out

# Replace unit_externalities_from_extracting() function definition with the following:
# _out = np.nan
#
# if annual_demand() == 0:
#     _out = 0
# else:
#     _out = externalities_from_extracting() / annual_demand()
#
# return _out

# Replace unit_externalities_from_total_transportation() function definition with the following:
# _out = np.nan
#
# if annual_demand() == 0:
#     _out = 0
# else:
#     _out = externalities_from_total_transportation() / annual_demand()
#
# return _out

# Replace unit_externalities_from_reusing() function definition with the following:
# _out = np.nan
#
# if annual_demand() == 0:
#     _out = 0
# else:
#     _out = externalities_from_reusing() / annual_demand()
#
# return _out

# Add data connection for average turbine capacity data
# Replace average_turbine_capacity_data() function definition with the following:
# capacity_data = read_csv('wind.csv',
#                          usecols=['year', 'avg turbine capacity mw'])
#
# return functions.lookup(time(),
#                         np.array(capacity_data['year']),
#                         np.array(capacity_data['avg turbine capacity mw']))

# Add data connection for installed capacity per year data
# Replace installed_capacity_per_year_data() function definition with the following:
# installation_data = read_csv('wind.csv', usecols=['year', 'mw installed'])
#
# return functions.lookup(time(),
#                         np.array(installation_data['year']),
#                         np.array(installation_data['mw installed']))

def simple_plot(result, names):
    """
    very basic plot function for quickly showing pysd model results
    :param result: Name of variable where pysd model results are stored
    :param names: Name of pysd model variables to plot
    :return:
    """

    plt.figure(1, figsize=(5, 5))
    plt.subplot(211)
    stock_names = names
    stocks = result[stock_names]
    plt.plot(stocks)
    plt.ylabel(stock_names[0])
    plt.xlabel('Time')
    plt.legend(stock_names)


# set parameters and initial conditions for steel; get results
steel = model.run(params={'scenario name':'steel base',
                          'material selection':'steel',
                          'fraction used product recycled initial value':0.30,
                          'fraction used product reused initial value':0,
                          'fraction used product remanufactured initial value':0,
                          'initial cost of reuse process':125,
                          'initial cost of remanufacturing process':250,
                          'initial cost of recycling process':200,
                          'initial cost of extracting':30,
                          'initial cost of manufacturing':35,
                          'extracting learning rate':0.05,
                          'manufacturing learning rate':0.05,
                          'reuse learning rate':0.05,
                          'remanufacture learning rate':0.05,
                          'recycle learning rate':0.05,
                          'recycle research annual cost reduction':0})

blade_lbd_no_rd = model.run(params={'scenario name':'blade_lbd_no_rd',
                                    'material selection':'glass fiber',
                                    'fraction used product recycled initial value':0,
                                    'initial cost of reuse process':100000,
                                    'initial cost of remanufacturing process':75000,
                                    'initial cost of recycling process':50000,
                                    'initial cost of extracting':25000,
                                    'initial cost of manufacturing':25000,
                                    'extracting learning rate':0.03,
                                    'manufacturing learning rate':0.03,
                                    'reused material strategic value':0,
                                    'remanufactured material strategic value':0,
                                    'recycled material strategic value':0,
                                    'reuse learning rate':0.05,
                                    'remanufacture learning rate':0.05,
                                    'recycle learning rate':0.05,
                                    'recycle research annual cost reduction':0})

blade_lbd_with_rd = model.run(params={'scenario name':'blade_lbd_with_rd',
                                      'material selection':'glass fiber',
                                      'fraction used product recycled initial value':0,
                                      'initial cost of reuse process':100000,
                                      'initial cost of remanufacturing process':75000,
                                      'initial cost of recycling process':50001,
                                      'initial cost of extracting':25000,
                                      'initial cost of manufacturing':25000,
                                      'extracting learning rate':0.03,
                                      'manufacturing learning rate':0.03,
                                      'reused material strategic value':0,
                                      'remanufactured material strategic value':0,
                                      'recycled material strategic value':0,
                                      'reuse learning rate':0.05,
                                      'remanufacture learning rate':0.05,
                                      'recycle learning rate':0.05,
                                      'recycle research annual cost reduction':0.003})


## Stepwise model running with default parameter settings
test_model = get_model(pysdfile)

first_step_results = first_step(test_model, init_time=1982, timestep=0.25, param_dict={'scenario name':'test-case'})

second_step_results = step(test_model, time=first_step_results[1], timestep=0.25)

third_step_results = step(test_model, time=second_step_results[1], timestep=0.25)

new_model = reset_model(test_model, pysdfile)


## Stepwise model running in a loop with a parameter value updated at every timestep
start_time=1982
final_time=1992
quarters=0.25

# load pySD model
loop_model=get_model(pysdfile)

# initialize parameter value
strat_val=0

# initialize model by running the first time step
first = first_step(loop_model, init_time=start_time, timestep=quarters, param_dict={'scenario name':'loop-case'})

# get the current model time from function output
model_time = first[1]

for i in np.arange(start_time+quarters, final_time+quarters, quarters):

    # wait for DES input to set parameter value

    step_results = step(loop_model,time=model_time,timestep=quarters,
                        param_dict={'remanufactured material strategic value':strat_val})

    model_time += quarters
    strat_val += 1

    # send output to DES model for use at next timestep