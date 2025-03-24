import copy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from input_data import InputData, generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity, zone_mapping
from model import Step3_zonal

def modify_atc(value):
    """Modify Available Transfer Capacity (ATC) and return updated input data."""
    modified_bus_capacity = bus_capacity.copy()
    return InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, modified_bus_capacity, zone_mapping, atc=value)

def modify_capacity(factor):
    """Modify bus capacities by a given factor and return updated input data."""
    modified_bus_capacity = {bus: cap * factor for bus, cap in bus_capacity.items()}
    return InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, modified_bus_capacity, zone_mapping)

def run_model(input_data):
    """Runs the zonal model and returns results."""
    model = Step3_zonal(input_data)
    model.run()
    return model.results

def sensitivity_analysis():
    # --- ATC Sensitivity Analysis ---
    print("=== Running ATC Sensitivity Analysis ===")
    atc_values = [0, 10, 50, 100, 200, 500, 1000]
    atc_zonal_prices = {zone: [] for zone in ["Zone A", "Zone B"]}
    atc_social_welfare = []

    for atc in atc_values:
        print(f"\nRunning model with ATC = {atc} MW...")
        results = run_model(modify_atc(atc))
        
        for zone in ["Zone A", "Zone B"]:
            avg_price = np.mean([results.zonal_price.get((zone, h), 0) for h in range(1, 25)])
            atc_zonal_prices[zone].append(avg_price)
        atc_social_welfare.append(results.objective)

    # --- Capacity Sensitivity Analysis ---
    print("\n=== Running Capacity Sensitivity Analysis ===")
    capacity_factors = [0.8, 1.0, 1.2]  # -20%, original, +20%
    capacity_labels = ["-20% Capacity", "Original", "+20% Capacity"]
    cap_zonal_prices = {zone: [] for zone in ["Zone A", "Zone B"]}
    cap_social_welfare = []
    hourly_prices = {zone: {scenario: [] for scenario in capacity_labels} for zone in ["Zone A", "Zone B"]}

    for factor, label in zip(capacity_factors, capacity_labels):
        print(f"\nRunning model with {label}...")
        results = run_model(modify_capacity(factor))
        
        for zone in ["Zone A", "Zone B"]:
            # Store average prices for bar chart
            avg_price = np.mean([results.zonal_price.get((zone, h), 0) for h in range(1, 25)])
            cap_zonal_prices[zone].append(avg_price)
            
            # Store hourly prices for time series
            hourly_prices[zone][label] = [results.zonal_price.get((zone, h), 0) for h in range(1, 25)]
        
        cap_social_welfare.append(results.objective)

    # --- Plot Results ---
    plot_atc_results(atc_values, atc_zonal_prices, atc_social_welfare)
    plot_capacity_results(capacity_labels, cap_zonal_prices, cap_social_welfare, hourly_prices)

def plot_atc_results(atc_values, zonal_prices, social_welfare):
    """Plot ATC sensitivity results"""
    plt.figure(figsize=(12, 5))
    
    # Zonal Prices
    plt.subplot(1, 2, 1)
    for zone, prices in zonal_prices.items():
        plt.plot(atc_values, prices, marker="o", label=zone)
    plt.xlabel("ATC (MW)")
    plt.ylabel("Average Price ($/MWh)")
    plt.title("ATC Impact on Zonal Prices")
    plt.grid(True)
    plt.legend()
    
    # Social Welfare
    plt.subplot(1, 2, 2)
    plt.plot(atc_values, social_welfare, marker="o", color="purple")
    plt.xlabel("ATC (MW)")
    plt.ylabel("Social Welfare ($)")
    plt.title("ATC Impact on Social Welfare")
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

def plot_capacity_results(labels, zonal_prices, social_welfare, hourly_prices):
    """Plot capacity sensitivity results with custom markers for hourly prices"""
    
    # --- Hourly Price Curves with Custom Markers ---
    plt.figure(figsize=(12, 5))
    
    # Define custom markers and colors for each scenario
    scenario_styles = {
        "-20% Capacity": {"marker": "v", "color": "red", "linestyle": ":"},
        "Original": {"marker": "o", "color": "blue", "linestyle": "-"},
        "+20% Capacity": {"marker": "^", "color": "green", "linestyle": "--"}
    }
    
    for i, zone in enumerate(["Zone A", "Zone B"], 1):
        plt.subplot(1, 2, i)
        
        for scenario in labels:
            style = scenario_styles[scenario]
            plt.plot(range(1, 25), 
                    hourly_prices[zone][scenario], 
                    marker=style["marker"],
                    linestyle=style["linestyle"],
                    color=style["color"],
                    markersize=6,
                    markevery=2,  # Show markers every 2 points to avoid clutter
                    label=scenario)
        
        plt.xlabel("Hour")
        plt.ylabel("Price ($/MWh)")
        plt.title(f"{zone} Hourly Prices")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.xticks(range(1, 25, 3))
    
    plt.tight_layout()
    plt.show()
    
    # --- Keep the original bar charts (unchanged) ---
    plt.figure(figsize=(12, 5))
    
    # Zonal Prices Bar Chart
    plt.subplot(1, 2, 1)
    x = np.arange(len(labels))
    width = 0.35
    for i, zone in enumerate(["Zone A", "Zone B"]):
        bars = plt.bar(x + i*width, zonal_prices[zone], width, label=zone)
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.1f}',
                     ha='center', va='bottom')
    plt.xlabel("Capacity Scenario")
    plt.ylabel("Average Price ($/MWh)")
    plt.title("Capacity Impact on Prices")
    plt.xticks(x + width/2, labels)
    plt.grid(True, axis='y')
    plt.legend()
    
    # Social Welfare Bar Chart
    plt.subplot(1, 2, 2)
    bars = plt.bar(labels, social_welfare, color=['orange', 'blue', 'green'])
    plt.xlabel("Capacity Scenario")
    plt.ylabel("Social Welfare ($)")
    plt.title("Capacity Impact on Social Welfare")
    plt.grid(True, axis='y')
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'${height:,.0f}',
                 ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()
if __name__ == "__main__":
    sensitivity_analysis()