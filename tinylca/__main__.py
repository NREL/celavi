import sys
import os

import pysd
import matplotlib.pyplot as plt
import time

start = time.time()
model = pysd.load('sd_model.py')

# Show model documents after import to confirm it loaded
print(model.doc())

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

print(sys.path[0])
