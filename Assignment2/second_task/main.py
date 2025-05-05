import numpy as np
import pandas as pd # Needed for saving p_analysis
import gurobipy as gp # Keep Gurobi import for status codes

# Import necessary classes and functions from other modules
from input_data import InputData
from model_one_price import OnePriceBiddingModel
from model_two_price import TwoPriceBiddingModel
from model_p90_bidding import P90BiddingModel
from plotting import plot_results # Use the corrected plotting function

def main():
    print("\n" + "="*60)
    print(" STARTING ENERGY BIDDING STRATEGY ANALYSIS ".center(60, '='))
    print("="*60 + "\n")

    # =================================================================
    # 1. Initialize Input Data
    # =================================================================
    print("-" * 50)
    print("Initializing Input Data...".center(50))
    print("-" * 50)
    try:
        # Configure number of samples if needed, defaults are in InputData
        input_data = InputData(num_samples=200) # e.g., use 200 scenarios for models

        # Optional: Override default price factors if needed
        # input_data.positiveBalancePriceFactor = 0.85
        # input_data.negativeBalancePriceFactor = 1.15
        print(f"Using p_nom: {input_data.p_nom} kW")
        print(f"Using {len(input_data.W)} scenarios for stochastic models.")
        print(f"Probability per scenario: {input_data.prob_scenario:.4f}")
        print(f"Positive Balance Price Factor: {input_data.positiveBalancePriceFactor}")
        print(f"Negative Balance Price Factor: {input_data.negativeBalancePriceFactor}")

        if not input_data.scenarios:
             print("\nError: No scenarios loaded. Exiting.")
             return # Exit if data loading failed

    except Exception as e:
        print(f"\nError initializing InputData: {e}")
        return # Exit if initialization fails


    # =================================================================
    # 2. Run P90 Bidding Analysis (Deterministic Benchmarks)
    # =================================================================
    print("\n" + "-" * 50)
    print("Running P90 Bidding Analysis...".center(50))
    print("-" * 50)
    p90_model = None # Initialize to handle potential errors
    p90_results = {} # Default to empty dict
    try:
        p90_model = P90BiddingModel(input_data, verbose=False) # Set verbose=False to reduce console output
        p90_model.run()
        # Assign results if run was successful (even if bids are NaN)
        p90_results = p90_model.results
        print("P90 analysis complete.")
    except Exception as e:
        print(f"Error running P90 Model: {e}")
        # Continue if possible, or decide to exit


    # =================================================================
    # 3. Run Stochastic Bidding Models
    # =================================================================
    print("\n" + "-" * 50)
    print("Running One-Price Bidding Model...".center(50))
    print("-" * 50)
    one_price_model = None
    one_price_results = {} # Default to empty dict
    try:
        one_price_model = OnePriceBiddingModel(input_data, verbose=False)
        one_price_model.run()
        one_price_results = one_price_model.results # Get results regardless of status
        if one_price_model.model and one_price_model.model.status == gp.GRB.OPTIMAL:
            print("One-Price optimization complete.")
            # one_price_model.print_results() # Optionally print detailed results
        else:
            print("One-Price model did not solve optimally.")
    except Exception as e:
        print(f"Error running One-Price Model: {e}")

    print("\n" + "-" * 50)
    print("Running Two-Price Bidding Model...".center(50))
    print("-" * 50)
    two_price_model = None
    two_price_results = {} # Default to empty dict
    try:
        two_price_model = TwoPriceBiddingModel(input_data, verbose=False)
        two_price_model.run()
        two_price_results = two_price_model.results # Get results regardless of status
        if two_price_model.model and two_price_model.model.status == gp.GRB.OPTIMAL:
             print("Two-Price optimization complete.")
             # two_price_model.print_results() # Optionally print detailed results
        else:
             print("Two-Price model did not solve optimally.")
    except Exception as e:
        print(f"Error running Two-Price Model: {e}")


    # =================================================================
    # 4. Consolidate Results and Generate Plots/Summary
    # =================================================================
    print("\n" + "-"*50)
    print("Consolidating Results & Generating Summary...".center(50))
    print("-"*50)

    # Prepare results dictionary for plotting and summary using the captured results dicts
    results_summary = {
        'p90': p90_results,
        'one_price': one_price_results,
        'two_price': two_price_results
    }

    # --- Generate Plots ---
    try:
        # Pass the consolidated dictionary to the plotting function
        plot_results(results_summary, save_path='bidding_analysis_summary.png')
    except Exception as e:
         print(f"Error generating plots: {e}")


    # --- Print Final Summary Table ---
    print("\n" + "="*60)
    print(" FINAL RESULTS SUMMARY ".center(60, '='))
    print("="*60)

    # Use .get() chaining on the dictionaries for safe access
    p90_bid = results_summary.get('p90', {}).get('also_x_bid', np.nan)
    cvar_bid = results_summary.get('p90', {}).get('cvar_bid', np.nan)
    one_price_avg_bid = results_summary.get('one_price', {}).get('avg_bid', np.nan)
    two_price_avg_bid = results_summary.get('two_price', {}).get('avg_bid', np.nan)
    one_price_profit = results_summary.get('one_price', {}).get('profit', np.nan)
    two_price_profit = results_summary.get('two_price', {}).get('profit', np.nan)
    p90_success = results_summary.get('p90', {}).get('also_x_verification', {}).get('success_rate', np.nan)
    p90_exp_shortfall = results_summary.get('p90', {}).get('also_x_verification', {}).get('expected_shortfall', np.nan)

    # Create a DataFrame for cleaner summary output
    summary_data = {
        'Metric': [
            "P90 Bid (kW)",
            "CVaR (ES 90%) Bid (kW)",
            "One-Price Avg. Hourly Bid (kW)",
            "Two-Price Avg. Hourly Bid (kW)",
            "", # Separator
            "P90 Out-Sample Success Rate (%)",
            "P90 Out-Sample Expected Shortfall (kW)",
             "", # Separator
            "One-Price Total Expected Profit (€)",
            "Two-Price Total Expected Profit (€)",
        ],
        'Value': [
            f"{p90_bid:.2f}" if not np.isnan(p90_bid) else "N/A",
            f"{cvar_bid:.2f}" if not np.isnan(cvar_bid) else "N/A",
            f"{one_price_avg_bid:.2f}" if not np.isnan(one_price_avg_bid) else "N/A",
            f"{two_price_avg_bid:.2f}" if not np.isnan(two_price_avg_bid) else "N/A",
            "",
            f"{p90_success:.1f}" if not np.isnan(p90_success) else "N/A",
            f"{p90_exp_shortfall:.2f}" if not np.isnan(p90_exp_shortfall) else "N/A",
            "",
            f"{one_price_profit:.2f}" if not np.isnan(one_price_profit) else "N/A",
            f"{two_price_profit:.2f}" if not np.isnan(two_price_profit) else "N/A",
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False, header=False))
    print("="*60)


    # --- Save P-Analysis Data ---
    # Safely get the DataFrame using .get()
    p_analysis_df = results_summary.get('p90', {}).get('p_analysis', pd.DataFrame())
    if isinstance(p_analysis_df, pd.DataFrame) and not p_analysis_df.empty:
        try:
            p_analysis_output_path = 'p_level_requirement_analysis.csv'
            p_analysis_df.to_csv(p_analysis_output_path, index=False, float_format='%.2f')
            print(f"\nSaved P-level requirement analysis to '{p_analysis_output_path}'")
        except Exception as e:
            print(f"\nError saving P-level analysis to CSV: {e}")
    else:
        print("\nP-level analysis data not available or invalid to save.")

    print("\nAnalysis finished.")
    print("="*60)


if __name__ == "__main__":
    # Ensure Gurobi is installed and licensed if running stochastic models
    try:
         import gurobipy
         # Optional: Check license by creating a temporary environment
         # with gurobipy.Env(empty=True) as env: env.start()
         print("GurobiPy library found.")
    except ImportError:
         print("Warning: GurobiPy not found. Stochastic models (OnePrice, TwoPrice) will fail.")
    except gurobipy.GurobiError as e: # Catch potential Gurobi license errors on import/env creation
         print(f"Warning: Gurobi environment error: {e}. Stochastic models may fail.")
    except Exception as e:
         print(f"An unexpected error occurred related to Gurobi: {e}")

    main()