import copy
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
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
    Returns a DataFrame with hourly market prices for each scenario.
    """
    results = []

    for capacity in battery_capacities:
        for charge_rate in charging_rates:
            for discharge_rate in discharge_rates:
                for charge_eff in charge_efficiencies:
                    for discharge_eff in discharge_efficiencies:

                        modified_input = base_input_data
                        
                        # Update battery parameters
                        modified_input.max_battery_storage = capacity
                        modified_input.max_battery_charging_power = charge_rate
                        modified_input.max_battery_discharging_power = discharge_rate
                        modified_input.battery_charge_efficiency = charge_eff
                        modified_input.battery_discharge_efficiency = discharge_eff

                        # Run the model with modified parameters
                        model = Step2_model(modified_input)
                        model.run()

                        # Extract hourly market prices and store as a list
                        
                        hourly_prices = list(model.results.price.values())
                        results.append({
                            "Battery Capacity (MWh)": capacity,
                            # "Charging Rate (MW)": charge_rate,
                            # "Discharging Rate (MW)": discharge_rate,
                            # "Charge Efficiency": charge_eff,
                            # "Discharge Efficiency": discharge_eff,
                            "Market Price ($/MWh)": hourly_prices,
                            "Hour": list(model.data.timeSpan),
                        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    # Initialize the base InputData object (as done in your main.py)
    input_data = InputData(
        generators=generators,  # From your data
        bid_offers=bid_offers,
        demand=system_demand,
        demand_per_load=demand_per_load,
        p_initial=p_initial,
    )

    # Define parameter ranges to test
    battery_params = {
        "battery_capacities": [0, 450],  # MWh
        "charging_rates": [300],  # MW (same for both scenarios)
        "discharge_rates": [300],  # MW (same for both scenarios)
        "charge_efficiencies": [0.95],  # Same for both scenarios
        "discharge_efficiencies": [0.95],  # Same for both scenarios
    }

    # Run sensitivity analysis
    results_df = run_battery_sensitivity(input_data, **battery_params)    

    # Plot hourly prices for battery ON and OFF scenarios
    if not results_df.empty:

        # Filter results for battery OFF (capacity = 0)
        battery_off_df = results_df[
            (results_df["Battery Capacity (MWh)"] == 0)
        ]
        hours_off = battery_off_df['Hour'].explode().tolist()
        prices_off = battery_off_df['Market Price ($/MWh)'].explode().tolist()

        # Filter results for battery ON (capacity = 200)
        battery_on_df = results_df[
            (results_df["Battery Capacity (MWh)"] == 450)
        ]
        hours_on = battery_on_df['Hour'].explode().tolist()
        prices_on = battery_on_df['Market Price ($/MWh)'].explode().tolist()

        # Plot both scenarios on the same graph with transparency
        plt.figure(figsize=(10, 6))
        plt.plot(
            hours_off, prices_off,
            color="red", label="Battery OFF (0 MWh)", alpha=0.6, marker = '^', markerfacecolor='none'
        )

        # Plot battery ON scenario (step plot)
        plt.plot(
            hours_on, prices_on,
            color="blue", label="Battery ON (450 MWh)", alpha=0.4, marker = 'o', markerfacecolor='none'
        )
        
        plt.xlabel("Hour")
        plt.ylabel("Market Price ($/MWh)")
        plt.title("Hourly Market-Clearing Prices: Battery ON vs. OFF")
        plt.legend()
        plt.grid(True)
        plt.show()

# something so the plots are shown even if they are the same values.
