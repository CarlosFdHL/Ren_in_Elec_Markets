"""
class InputData:
    def __init__(self):
        self.max_battery_storage = 0
        self.max_battery_charging_power = 0
        self.max_battery_discharging_power = 0
        self.battery_charge_efficiency = 0
        self.battery_discharge_efficiency = 0

class Step2_model:
    def __init__(self, input_data):
        self.input_data = input_data
        self.results = None
        self.variables = None

    def run(self):
        # Implement the model execution logic here
        # Populate self.results and self.variables with the necessary data
        self.results = {
            'objective': 0,  # Example objective value
            'price': [],  # Example market clearing prices
            'production_data': [],  # Example production data
            'profit_data': [],  # Example profit data
            'utility': [],  # Example utility data
        }
        self.variables = {
            'stored_energy': {}  # Example stored energy data
        }
"""
import copy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from input_data import InputData, generators, bid_offers, system_demand, demand_per_load, p_initial
from model import Step2_model

def run_battery_sensitivity(
    base_input_data: InputData,
    battery_capacities: list,
    charging_rates: list,
    discharge_rates: list,
    charge_efficiencies: list,
    discharge_efficiencies: list,
):
    """
    Run sensitivity analysis by modifying battery parameters in the InputData object.
    """
    results = []

    for capacity in battery_capacities:
        for charge_rate in charging_rates:
            for discharge_rate in discharge_rates:
                for charge_eff in charge_efficiencies:
                    for discharge_eff in discharge_efficiencies:
                        # Create a DEEP COPY of the input data to avoid modifying the original
                        modified_input = copy.deepcopy(base_input_data)
                        
                        # Update battery parameters
                        modified_input.max_battery_storage = capacity
                        modified_input.max_battery_charging_power = charge_rate
                        modified_input.max_battery_discharging_power = discharge_rate
                        modified_input.battery_charge_efficiency = charge_eff
                        modified_input.battery_discharge_efficiency = discharge_eff

                        # Run the model with modified parameters
                        model = Step2_model(modified_input)
                        model.run()

                        # Extract results
                        results.append({
                            "Battery Capacity (MWh)": capacity,
                            "Charging Rate (MW)": charge_rate,
                            "Discharging Rate (MW)": discharge_rate,
                            "Charge Efficiency": charge_eff,
                            "Discharge Efficiency": discharge_eff,
                            "Objective Value ($)": model.results.objective,
                            "Avg Market Price ($/MWh)": sum(model.results.price.values()) / len(model.results.price),
                            "Total Production (MW)": model.results.sum_power,
                        })

    return pd.DataFrame(results)

# Example usage in your main.py:
if __name__ == "__main__":
    # Initialize the base InputData object (as done in your main.py)
    # Replace this with your actual InputData initialization
    input_data = InputData(
        generators= generators,  # From your data
        bid_offers= bid_offers,
        demand=system_demand,
        demand_per_load=demand_per_load,
        p_initial=p_initial,
    )

    # Define parameter ranges to test
    battery_params = {
        "battery_capacities": [100, 200, 300],  # MWh
        "charging_rates": [50, 100, 150],  # MW
        "discharge_rates": [50, 100, 150],  # MW
        "charge_efficiencies": [0.8, 0.9, 0.95],
        "discharge_efficiencies": [0.8, 0.9, 0.95],
    }

    # Run sensitivity analysis
    results_df = run_battery_sensitivity(input_data, **battery_params)

    # Save results to CSV
    results_df.to_csv("battery_sensitivity_results.csv", index=False)
    print(results_df)