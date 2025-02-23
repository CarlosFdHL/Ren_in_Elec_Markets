import matplotlib.pyplot as plt
import numpy as np


def plotting_results(model):
# Plotting the results of the optimization problem
    t, price = zip(*model.results.price.items())
    plt.step(t, price)
    plt.xlabel("Hour")
    plt.ylabel("Price $/MWh")
    plt.title("Market clearing price for each hour")
    plt.show()

    _, stored_energy = zip(*model.variables.stored_energy.items())
    stored_energy = [float(value.X) for value in stored_energy]
    plt.step(t, stored_energy)
    plt.xlabel("Hour")
    plt.ylabel("Energy stored MWh")
    plt.title("Energy stored in battery for each hour")
    plt.xticks(range(1, 25))
    plt.show()