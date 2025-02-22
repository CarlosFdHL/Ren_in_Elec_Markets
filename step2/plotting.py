import matplotlib.pyplot as plt
import numpy as np


def plotting_results(model):
# Plotting the results of the optimization problem
    t, price = zip(*model.results.price.items())
    plt.plot(t, price)
    plt.xlabel("Hour")
    plt.ylabel("Price $/MWh")
    plt.title("Market clearing price for each hour")
    plt.show()