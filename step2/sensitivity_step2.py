import copy
import pandas as pd
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

                        # Extract hourly market prices
                        hourly_prices = model.results.price

                        # Store results for each hour
                        for hour, price in hourly_prices.items():
                            results.append({
                                "Battery Capacity (MWh)": capacity,
                                "Charging Rate (MW)": charge_rate,
                                "Discharging Rate (MW)": discharge_rate,
                                "Charge Efficiency": charge_eff,
                                "Discharge Efficiency": discharge_eff,
                                "Hour": hour,
                                "Market Price ($/MWh)": price,
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
        "charging_rates": [100, 300],  # MW (same for both scenarios)
        "discharge_rates": [100, 300],  # MW (same for both scenarios)
        "charge_efficiencies": [0.95],  # Same for both scenarios
        "discharge_efficiencies": [0.95],  # Same for both scenarios
    }

    # Run sensitivity analysis
    results_df = run_battery_sensitivity(input_data, **battery_params)

    # Save results to CSV
    results_df.to_csv("hourly_price_sensitivity_results.csv", index=False)
    print(results_df)
    

    # Plot hourly prices for battery ON and OFF scenarios
    if not results_df.empty:
        # Filter results for battery OFF (capacity = 0)
        battery_off_df = results_df[
            (results_df["Battery Capacity (MWh)"] == 0)
        ]

        # Filter results for battery ON (capacity = 200)
        battery_on_df = results_df[
            (results_df["Battery Capacity (MWh)"] == 450)
        ]

        # Plot both scenarios on the same graph with transparency
        plt.figure(figsize=(10, 6))
        plt.scatter(
            battery_off_df["Hour"], battery_off_df["Market Price ($/MWh)"],
            color="red", label="Battery OFF (0 MWh)", alpha=0.9
        )

        # Plot battery ON scenario (step plot)
        plt.scatter(
            battery_on_df["Hour"], battery_on_df["Market Price ($/MWh)"],
            color="blue", label="Battery ON (450 MWh)", alpha=0.2
        )
        
        plt.xlabel("Hour")
        plt.ylabel("Market Price ($/MWh)")
        plt.title("Hourly Market-Clearing Prices: Battery ON vs. OFF")
        plt.legend()
        plt.grid(True)
        plt.show()

# something so the plots are shown even if they are the same values.
