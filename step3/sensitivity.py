import copy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from input_data import InputData, generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity
from main import run_model  # Ensure this returns meaningful data

def modify_capacity(factor):
    # Create a new modified version of bus reactance
    modified_bus_capacity = {key: value * factor for key, value in bus_capacity.items()}
    return InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, modified_bus_capacity)

def sensitivity_analysis():
    # Original input data
    original_input_data = InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity)
    
    # Run model and store results
    print("Running model with original capacity values...")
    results_original = run_model(original_input_data) 

    increased_capacity_data = modify_capacity(0.8)
    print("\nRunning model with increased capacity values (+20%)...")
    results_increased = run_model(increased_capacity_data) 

    decreased_capacity_data = modify_capacity(1.2)
    print("\nRunning model with decreased capacity values (-20%)...")
    results_decreased = run_model(decreased_capacity_data)

    
    plot_nodal_prices(results_original, results_increased, results_decreased)

def plot_nodal_prices(results_original, results_increased, results_decreased):
    # Extract all unique buses and hours
    nodes = sorted(set(n for (n, _) in results_original.keys()))
    hours = sorted(set(t for (_, t) in results_original.keys()))
    
    # Create a figure for each hour
    for display_hour in hours:
        # Get data for this hour
        prices_original = [results_original.get((bus, display_hour), 0) for bus in nodes]
        prices_increased = [results_increased.get((bus, display_hour), 0) for bus in nodes]
        prices_decreased = [results_decreased.get((bus, display_hour), 0) for bus in nodes]
        
        # Set up the plot
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Set width and positions
        bar_width = 0.25
        index = np.arange(len(nodes))
        
        # Create bars for each scenario
        rects1 = ax.bar(index - bar_width, prices_original, bar_width, 
                        label='Original', color='blue', alpha=0.7)
        rects2 = ax.bar(index, prices_increased, bar_width, 
                        label='Increased Capacity (+20%)', color='green', alpha=0.7)
        rects3 = ax.bar(index + bar_width, prices_decreased, bar_width, 
                        label='Decreased Capacity (-20%)', color='red', alpha=0.7)
        
        # Add labels, title and legend
        ax.set_xlabel('Node')
        ax.set_ylabel('Nodal Price ($/MWh)')
        ax.set_title(f'Nodal Price Comparison at Hour {display_hour}')
        ax.set_xticks(index)
        ax.set_xticklabels([f'{bus}' for bus in nodes])
        ax.legend()
        
        # Add grid lines for better readability
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        
        # Add value labels on top of bars
        def add_labels(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', rotation=90, fontsize=8)
        
        # Uncomment these if you want value labels (can be crowded with many nodes)
        # add_labels(rects1)
        # add_labels(rects2)
        # add_labels(rects3)
        
        plt.tight_layout()
       # plt.savefig(f'nodal_prices_hour_{display_hour}.png')
        plt.show()
'''   
    # Create a summary plot with average prices across all hours
    avg_original = []
    avg_increased = []
    avg_decreased = []
    
    for bus in nodes:
        avg_original.append(np.mean([results_original.get((bus, h), 0) for h in hours]))
        avg_increased.append(np.mean([results_increased.get((bus, h), 0) for h in hours]))
        avg_decreased.append(np.mean([results_decreased.get((bus, h), 0) for h in hours]))
    
    # Set up the summary plot
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Create bars for each scenario
    rects1 = ax.bar(index - bar_width, avg_original, bar_width, 
                    label='Original', color='blue', alpha=0.7)
    rects2 = ax.bar(index, avg_increased, bar_width, 
                    label='Increased Capacity (+20%)', color='green', alpha=0.7)
    rects3 = ax.bar(index + bar_width, avg_decreased, bar_width, 
                    label='Decreased Capacity (-20%)', color='red', alpha=0.7)
    
    # Add labels, title and legend for summary plot
    ax.set_xlabel('Node')
    ax.set_ylabel('Average Nodal Price ($/MWh)')
    ax.set_title('Average Nodal Price Comparison Across All Hours')
    ax.set_xticks(index)
    ax.set_xticklabels([f'{bus}' for bus in nodes])
    ax.legend()
    
    # Add grid lines for better readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()
'''
if __name__ == "__main__":
    sensitivity_analysis()
