import pysd
import matplotlib.pyplot as plt
import time

# Read in Vensim model: national scale, adjusted for import
model = pysd.read_vensim("C://Users//rhanes//Documents//GitHub//tiny-lca//tinysd//vensim model//national-scale//tiny-sd-all-US.mdl")  # use for first load of model from Vensim

start = time.time()
model = pysd.load('tiny-sd_pysd_v13may2020.py')

# Show model documents after import to confirm it loaded
# print(model.doc())

# Run model and collect the result
# other stocks: 'Raw Material Extraction'
result = model.run()
end = time.time()
print("Run time (s):", round(end - start, 2))

# Plot results
plt.figure(1, figsize=(5, 8))
plt.subplot(211)
stock_names = ['Products at End of Life', 'Product Remanufacture',
               'Material Recycle', 'Product Reuse', 'Landfill and Incineration',
               'Products in Use']
stocks = result[stock_names]
plt.plot(stocks)
plt.ylabel('Mass (kg)')
plt.xlabel('Months')

plt.subplot(212)
relative_landfill = result['relative landfill']
plt.plot(relative_landfill)
plt.ylabel('Relative Landfill')
plt.xlabel('Months')
plt.show()