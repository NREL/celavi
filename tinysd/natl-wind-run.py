import pysd
import matplotlib.pyplot as plt

# Read in Vensim model: national scale, adjusted for import
# model = pysd.read_vensim("C://Users//rhanes//Documents//GitHub//tiny-lca//tinysd//vensim model//national-scale//natl-wind-importable.mdl")  # use for first load of model from Vensim

# load model if not converting afresh
model = pysd.load("C://Users//rhanes//Documents//GitHub//tiny-lca//tinysd//vensim model//national-scale//natl-wind-importable.py")

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

# Plot results
# plt.figure(1, figsize=(5, 8))
# plt.subplot(211)
# stock_names = ['Products at End of Life', 'Product Remanufacture',
#                'Material Recycle', 'Product Reuse', 'Landfill and Incineration',
#                'Products in Use']
# stocks = result[stock_names]
# plt.plot(stocks)
# plt.ylabel('Mass (kg)')
# plt.xlabel('Months')
#
# plt.subplot(212)
# relative_landfill = result['relative landfill']
# plt.plot(relative_landfill)
# plt.ylabel('Relative Landfill')
# plt.xlabel('Months')
# plt.show()

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