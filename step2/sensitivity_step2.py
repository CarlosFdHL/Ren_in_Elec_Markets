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
from input_data import InputData

def run_sensitivity_analysis(input_data, battery_capacities, charging_rates, discharge_rates, charge_efficiencies, discharge_efficiencies):
    """
    Run sensitivity analysis by manipulating battery parameters and running the model.

    Parameters:
    - input_data: Instance of InputData class containing the initial data.
    - battery_capacities: List of battery capacities to test.
    - charging_rates: List of maximum charging rates to test.
    - discharge_rates: List of maximum discharging rates to test.
    - charge_efficiencies: List of charging efficiencies to test.
    - discharge_efficiencies: List of discharging efficiencies to test.
    """
    results = []

    for capacity in battery_capacities:
        for charge_rate in charging_rates:
            for discharge_rate in discharge_rates:
                for charge_eff in charge_efficiencies:
                    for discharge_eff in discharge_efficiencies:
                        # Modify the battery parameters in the input data
                        input_data.max_battery_storage = capacity
                        input_data.max_battery_charging_power = charge_rate
                        input_data.max_battery_discharging_power = discharge_rate
                        input_data.battery_charge_efficiency = charge_eff
                        input_data.battery_discharge_efficiency = discharge_eff

                        # Initialize and run the model
                        model = Step2_model(input_data)
                        model.run()

                        # Save the results
                        results.append({
                            'Battery Capacity': capacity,
                            'Charging Rate': charge_rate,
                            'Discharging Rate': discharge_rate,
                            'Charging Efficiency': charge_eff,
                            'Discharging Efficiency': discharge_eff,
                            'Objective Value': model.results.objective,
                            'Market Clearing Prices': model.results.price,
                            'Production Data': model.results.production_data,
                            'Profit Data': model.results.profit_data,
                            'Utility Data': model.results.utility,
                            'Stored Energy': [v.X for v in model.variables.stored_energy.values()]
                        })

    # Convert results to a DataFrame for easier analysis
    results_df = pd.DataFrame(results)
    return results_df

# Example usage
if __name__ == "__main__":
    from input_data import InputData  # Ensure you import the InputData class

    # Initialize input data
    input_data = InputData()  # Replace with actual initialization if needed

    # Define ranges for sensitivity analysis
    battery_capacities = [100, 200, 300]  # Example battery capacities (MWh)
    charging_rates = [50, 100, 150]  # Example charging rates (MW)
    discharge_rates = [50, 100, 150]  # Example discharging rates (MW)
    charge_efficiencies = [0.8, 0.9, 1.0]  # Example charging efficiencies
    discharge_efficiencies = [0.8, 0.9, 1.0]  # Example discharging efficiencies

    # Run sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(input_data, battery_capacities, charging_rates, discharge_rates, charge_efficiencies, discharge_efficiencies)

    # Save or print the results
    sensitivity_results.to_csv("sensitivity_analysis_results.csv", index=False)
    print(sensitivity_results)