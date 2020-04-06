import pysd
import matplotlib.pyplot as plt
model = pysd.read_vensim('test_model.mdl')

print(model.doc())

stocks = model.run(return_columns=['Tea Cup Temperature', 'Room Temperature'])

stocks.plot()
plt.ylabel('Degrees F')
plt.xlabel('Minutes')
plt.show()