import copy
from input_data import InputData, generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity
from main import run_model  # Import the refactored function

def modify_capacity(input_data, factor):
    
    modified_data = input_data
    
    # Modify the bus capacity values by the given factor
    for key in modified_data.bus_reactance:
        modified_data.bus_reactance[key] *= factor
    
    return modified_data
# to change the capacity of the buses, we need to modify the bus_reactance values in the input data.
# The bus_reactance values are used to calculate the capacity of the lines in the model.
# Capacity = 1 / (reactance * 2)
# Therefore, to increase the capacity of the lines by 20%, we need to decrease the reactance values by 20%.
# Similarly, to decrease the capacity of the lines by 20%, we need to increase the reactance values by 20%. 

def sensitivity_analysis():
    # Original input data
    original_input_data = InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity)
    
    # Run the model with the original capacity values
    print("Running model with original capacity values...")
    run_model(original_input_data)
    
    # Modify capacity by +20% and run the model
    increased_capacity_data = modify_capacity(original_input_data, 0.8)
    print("\nRunning model with increased capacity values (+20%)...")
    run_model(increased_capacity_data)
    
    # Modify capacity by -20% and run the model
    decreased_capacity_data = modify_capacity(original_input_data, 1.2)
    print("\nRunning model with decreased capacity values (-20%)...")
    run_model(decreased_capacity_data)

if __name__ == "__main__":
    sensitivity_analysis()