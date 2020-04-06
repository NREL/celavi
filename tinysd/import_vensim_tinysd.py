import pysd
import matplotlib.pyplot as plt
# model = pysd.read_vensim('tiny-sd copy.mdl')  # use for first load of model from Vensim

model = pysd.load('tiny-sd_pysd_v30mar2020.py')

print(model.doc())

# other stocks: 'Raw Material Extraction'

result = model.run(return_columns=['relative landfill', 'Products at End of Life', 'Product Remanufacture', 'Material Recycle', 'Product Reuse', 'Landfill and Incineration', 'Products in Use'])

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