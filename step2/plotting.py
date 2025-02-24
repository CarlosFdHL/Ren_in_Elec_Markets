import matplotlib.pyplot as plt
import numpy as np


def plotting_results(model):
# Plotting the results of the optimization problem
    t, price = zip(*model.results.price.items())

    fig, ax = plt.subplots()
    ax.plot(t, price)
    ax.set_xlabel("Hour")
    ax.set_ylabel("Price $/MWh")
    ax.set_title("Market clearing price for each hour")

    _, stored_energy = zip(*model.variables.stored_energy.items())
    fig, ax = plt.subplots()
    stored_energy = [float(value.X) for value in stored_energy]
    ax.step(t, stored_energy)
    ax.set_xlabel("Hour")
    ax.set_ylabel("Energy stored MWh")
    ax.set_title("Energy stored in battery for each hour")
    ax.set_xticks(range(1, 25))
    
    
    plt.show()