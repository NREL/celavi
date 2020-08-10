import os
import shutil
import pysd
import matplotlib.pyplot as plt


vensimdir = os.getcwd() + "\\vensim\\national-scale\\"
pysdfile = 'natl-wind-importable.py'

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


# set parameters and initial conditions for steel; get results
steel = model.run(params={'material selection':1,
                          'fraction used product recycled initial value':0.30,
                          'fraction used product reused initial value':0,
                          'fraction used product remanufactured initial value':0,
                          'initial cost of reuse process':125,
                          'initial cost of remanufacturing process':250,
                          'initial cost of recycling process':200,
                          'initial cost of extraction and production':65,
                          'extraction and production learning rate':0.05,
                          'reuse learning rate':0.05,
                          'remanufacture learning rate':0.05,
                          'recycle learning rate':0.05,
                          'recycle research annual cost reduction':0})

blade_lbd_no_rd = model.run(params={'material selection':0,
                                    'fraction used product recycled initial value':0,
                                    'initial cost of reuse process':100000,
                                    'initial cost of remanufacturing process':75000,
                                    'initial cost of recycling process':50000,
                                    'initial cost of extraction and production':50000,
                                    'extraction and production learning rate':0.03,
                                    'reused material strategic value':0,
                                    'remanufactured material strategic value':0,
                                    'recycled material strategic value':0,
                                    'reuse learning rate':0.05,
                                    'remanufacture learning rate':0.05,
                                    'recycle learning rate':0.05,
                                    'recycle research annual cost reduction':0})

blade_lbd_with_rd = model.run(params={'material selection':0,
                                      'fraction used product recycled initial value':0,
                                      'initial cost of reuse process':100000,
                                      'initial cost of remanufacturing process':75000,
                                      'initial cost of recycling process':50001,
                                      'initial cost of extraction and production':50000,
                                      'extraction and production learning rate':0.03,
                                      'reused material strategic value':0,
                                      'remanufactured material strategic value':0,
                                      'recycled material strategic value':0,
                                      'reuse learning rate':0.05,
                                      'remanufacture learning rate':0.05,
                                      'recycle learning rate':0.05,
                                      'recycle research annual cost reduction':0.003})