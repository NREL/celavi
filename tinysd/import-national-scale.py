import pysd
import matplotlib.pyplot as plt

# Read in Vensim model: national scale, adjusted for import
# model = pysd.read_vensim("C://Users//rhanes//Documents//GitHub//tiny-lca//tinysd//vensim model//national-scale//natl-wind-importable.mdl")  # use for first load of model from Vensim

# load model if not converting afresh
model = pysd.load("tinysd/vensim model/national-scale/natl-wind-importable.py")

# Show model documents after import to confirm it loaded
# print(model.doc())

# does the model in python format run?
result = model.run()

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

print(result.columns)

time_series = result[['rate of increasing recycle fraction',
                      'rate of increasing reuse fraction',
                      'rate of increasing remanufacture fraction']]
xs = range(len(time_series))

fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(5, 15))
axs[0].plot(xs, time_series['rate of increasing recycle fraction'])
axs[0].set_title('rate of increasing recycle fraction')

axs[1].plot(xs, time_series['rate of increasing reuse fraction'])
axs[1].set_title('rate of increasing reuse fraction')

axs[2].plot(xs, time_series['rate of increasing remanufacture fraction'])
axs[2].set_title('rate of increasing remanufacture fraction')

plt.show()
