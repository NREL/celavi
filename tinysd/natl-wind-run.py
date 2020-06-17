import pysd
import matplotlib.pyplot as plt

# load model if not converting afresh
model = pysd.load('natl-wind-importable.py')

# Show model documents after import to confirm it loaded
# print(model.doc())

# set parameters and initial conditions for steel; get results
steel_result = model.run(params={'material selection':1,
                                 'fraction used product recycled initial value':0.30,
                                 'initial cost of reuse process':125,
                                 'initial cost of remanufacturing process':250,
                                 'initial cost of recycling process':200,
                                 'initial cost of extraction and production':65,
                                 'annual change in cost of extraction and production':-0.357,
                                 'reuse learning rate':-0.001,
                                 'remanufacture learning rate':-0.005,
                                 'recycle learning rate':-0.05})

blade_lowcostrecycle_result = model.run(params={'material selection':0,
                                                'fraction used product recycled initial value':0,
                                                'initial cost of reuse process':100000,
                                                'initial cost of remanufacturing process':75000,
                                                'initial cost of recycling process':50000,
                                                'initial cost of extraction and production':50000,
                                                'annual change in cost of extraction and production':-559,
                                                'reused material strategic value':0,
                                                'remanufactured material strategic value':0,
                                                'recycled material strategic value':2000,
                                                'reuse learning rate':-0.001,
                                                'remanufacture learning rate':-0.005,
                                                'recycle learning rate':-0.05})

blade_highcostrecycle_result = model.run(params={'material selection':0,
                                                'fraction used product recycled initial value':0,
                                                'initial cost of reuse process':100000,
                                                'initial cost of remanufacturing process':75000,
                                                'initial cost of recycling process':55000,
                                                'initial cost of extraction and production':50000,
                                                'annual change in cost of extraction and production':-559,
                                                'reused material strategic value':0,
                                                'remanufactured material strategic value':0,
                                                'recycled material strategic value':0,
                                                'reuse learning rate':-0.001,
                                                'remanufacture learning rate':-0.005,
                                                'recycle learning rate':-0.05})

# Plot blade, low cost recycle, scenario results
plt.figure(1, figsize=(5, 5))
plt.subplot(211)
stock_names = ['Fraction Recycle', 'Fraction Remanufacture', 'Fraction Reuse']
stocks = blade_lowcostrecycle_result[stock_names]
plt.plot(stocks)
plt.ylabel('Circularity Fractions')
plt.xlabel('Year')

blade_lowcostrecycle_result[1982:1990]['recycle process learning']

#blade_lowcostrecycle_result[1982:1990]['Cumulative Recycle']

def simple_plot(names):

    plt.figure(1, figsize=(5, 5))
    plt.subplot(211)
    stock_names = names
    stocks = blade_lowcostrecycle_result[stock_names]
    plt.plot(stocks)
    plt.ylabel(stock_names[0])
    plt.xlabel('Time')

plt.subplot(212)
relative_landfill = blade_lowcostrecycle_result['relative landfill']
plt.plot(relative_landfill)
plt.ylabel('Relative Landfill')
plt.xlabel('Months')
plt.show()

for col in result.columns:
    print(col)

time_series = result[['Fraction Recycle', 'Fraction Remanufacture', 'Fraction Reuse']]
xs = range(len(time_series))

fig, axs = plt.subplots(nrows=len(time_series.columns), ncols=1, figsize=(10, 7))
plt.tight_layout()
for i, col in enumerate(time_series):
    axs[i].plot(xs, time_series[col])
    axs[i].set_title(col)

plt.show()
