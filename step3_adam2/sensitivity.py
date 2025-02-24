import copy
from input_data import InputData, generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity
from main import run_model  # Import the refactored function

def modify_capacity(factor):
    # Create a new modified version of bus reactance
    modified_bus_reactance = {key: value * factor for key, value in bus_reactance.items()}
    
    return InputData(generators, bid_offers, system_demand, demand_per_load, modified_bus_reactance, bus_capacity)

def sensitivity_analysis():
    # Original input data
    original_input_data = InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity)
    
    print("Running model with original capacity values...")
    print("Bus Reactance:", original_input_data.bus_reactance)  # Debugging
    run_model(original_input_data)
    
    # Modify capacity by +20% and run the model
    increased_capacity_data = modify_capacity(0.8)
    print("\nRunning model with increased capacity values (+20%)...")
    print("Bus Reactance:", increased_capacity_data.bus_reactance)  # Debugging
    run_model(increased_capacity_data)
    
    # Modify capacity by -20% and run the model
    decreased_capacity_data = modify_capacity(1.2)
    print("\nRunning model with decreased capacity values (-20%)...")
    print("Bus Reactance:", decreased_capacity_data.bus_reactance)  # Debugging
    run_model(decreased_capacity_data)

if __name__ == "__main__":
    sensitivity_analysis()
