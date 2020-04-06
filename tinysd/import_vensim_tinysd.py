import pysd
import matplotlib.pyplot as plt
import time

# Import model (or read original Vensim model)
# model = pysd.read_vensim('tiny-sd copy.mdl')  # use for first load of model from Vensim

start = time.time()
model = pysd.load('tiny-sd_pysd_v30mar2020.py')

# Show model documents after import to confirm it loaded
# print(model.doc())

# Run model and collect the result
# other stocks: 'Raw Material Extraction'
result = model.run(return_columns=['relative landfill', 'Products at End of Life', 'Product Remanufacture', 'Material Recycle', 'Product Reuse', 'Landfill and Incineration', 'Products in Use'])
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