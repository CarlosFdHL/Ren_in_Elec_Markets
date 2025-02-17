import copy
from input_data import InputData, generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity
from main import run_model  # Import the refactored function

def modify_capacity(input_data, factor):
    # Create a deep copy of the input data to avoid modifying the original
    modified_data = copy.deepcopy(input_data)
    
    # Modify the bus capacity values by the given factor
    for key in modified_data.bus_capacity:
        modified_data.bus_capacity[key] *= factor
    
    return modified_data

def sensitivity_analysis():
    # Original input data
    original_input_data = InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity)
    
    # Run the model with the original capacity values
    print("Running model with original capacity values...")
    run_model(original_input_data)
    
    # Modify capacity by +20% and run the model
    increased_capacity_data = modify_capacity(original_input_data, 1.2)
    print("\nRunning model with increased capacity values (+20%)...")
    run_model(increased_capacity_data)
    
    # Modify capacity by -20% and run the model
    decreased_capacity_data = modify_capacity(original_input_data, 0.8)
    print("\nRunning model with decreased capacity values (-20%)...")
    run_model(decreased_capacity_data)

if __name__ == "__main__":
    sensitivity_analysis()