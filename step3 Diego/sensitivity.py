import copy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from input_data import InputData, generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity, zone_mapping
from model import Step3_zonal  # Ensure correct import of the model

def modify_atc(value):
    """Modify Available Transfer Capacity (ATC) and return updated input data."""
    modified_bus_capacity = bus_capacity.copy()  # Keep bus capacity unchanged
    return InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, modified_bus_capacity, zone_mapping, atc=value)

def run_model(input_data):
    """Runs the zonal model and returns results."""
    model = Step3_zonal(input_data)
    model.run()
    return model.results  # Return results object

def sensitivity_analysis():
    # Define the range of ATC values to test
    atc_values = [0, 10, 50, 100, 200, 500, 1000]

    # Storage for results
    zonal_prices = {zone: [] for zone in ["Zone A", "Zone B"]}
    social_welfare = []

    # Run the model for each ATC value
    for atc in atc_values:
        print(f"\nRunning model with ATC = {atc} MW...")
        modified_input_data = modify_atc(atc)
        results = run_model(modified_input_data)

        # Store zonal prices
        for zone in ["Zone A", "Zone B"]:
            avg_price = np.mean([results.zonal_price.get((zone, h), 0) for h in range(1, 25)])
            zonal_prices[zone].append(avg_price)

        # Store social welfare
        social_welfare.append(results.objective)

    # Plot results
    plot_zonal_prices(atc_values, zonal_prices)
    plot_social_welfare(atc_values, social_welfare)

def plot_zonal_prices(atc_values, zonal_prices):
    """Plots how zonal prices change with different ATC values."""
    plt.figure(figsize=(12, 6))

    for zone, prices in zonal_prices.items():
        plt.plot(atc_values, prices, marker="o", linestyle="-", label=f"{zone}")

    plt.xlabel("Available Transfer Capacity (MW)")
    plt.ylabel("Zonal Price ($/MWh)")
    plt.title("Impact of ATC on Zonal Prices")
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_social_welfare(atc_values, social_welfare):
    """Plots how social welfare changes with different ATC values."""
    plt.figure(figsize=(8, 5))

    plt.plot(atc_values, social_welfare, marker="o", linestyle="-", color="purple", label="Social Welfare")

    plt.xlabel("Available Transfer Capacity (MW)")
    plt.ylabel("Social Welfare ($)")
    plt.title("Impact of ATC on Social Welfare")
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    sensitivity_analysis()
