import matplotlib.pyplot as plt
import pandas as pd
import numpy as np # Needed for checking NaN

def plot_results(results: dict, save_path: str = 'results_summary.png'):
    """
    Generates summary plots for the bidding model results.

    Args:
        results (dict): A dictionary containing results from different models.
                        Expected keys: 'p90', 'one_price', 'two_price'.
                        Each key should map to a dictionary of results for that model.
        save_path (str): Path to save the generated plot image.
    """
    print(f"\nGenerating summary plot and saving to {save_path}...")

    fig, axs = plt.subplots(2, 2, figsize=(15, 12)) # Create a 2x2 grid of subplots
    fig.suptitle('Bidding Strategy Analysis Summary', fontsize=16)

    # --- Plot 1: P-Level Analysis (from p90 model) ---
    ax1 = axs[0, 0]
    # Safely get the p_analysis DataFrame using .get() with default empty DataFrame
    p_analysis_df = results.get('p90', {}).get('p_analysis', pd.DataFrame())

    # Check if DataFrame is not empty and has the required columns
    if not p_analysis_df.empty and all(col in p_analysis_df.columns for col in ['P_level', 'bid_kW', 'out_sample_success_rate_perc', 'out_sample_expected_shortfall_kW']):
        # Primary Y-axis: Bid Amount
        ax1.plot(p_analysis_df['P_level'], p_analysis_df['bid_kW'], 'o-', color='tab:blue', label='Bid Amount (kW)')
        ax1.set_xlabel('P-Level Requirement (%)')
        ax1.set_ylabel('Bid Amount (kW)', color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.grid(True, axis='x')

        # Secondary Y-axis: Success Rate & Expected Shortfall
        ax1b = ax1.twinx()
        ax1b.plot(p_analysis_df['P_level'], p_analysis_df['out_sample_success_rate_perc'], 's--', color='tab:green', label='Out-Sample Success Rate (%)')
        # ax1b.plot(p_analysis_df['P_level'], p_analysis_df['out_sample_expected_shortfall_kW'], '^:', color='tab:red', label='Out-Sample Exp. Shortfall (kW)') # Optional: Add shortfall
        ax1b.set_ylabel('Success Rate (%)', color='tab:green')
        # ax1b.set_ylabel('Success Rate (%) / Exp. Shortfall (kW)') # If including shortfall
        ax1b.tick_params(axis='y', labelcolor='tab:green')

        ax1.set_title('Bid Strategy vs. P-Level')
        # Combine legends
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1b.get_legend_handles_labels()
        ax1b.legend(lines + lines2, labels + labels2, loc='center right')
    else:
        ax1.text(0.5, 0.5, 'P-Analysis Data Missing or Invalid', horizontalalignment='center', verticalalignment='center', transform=ax1.transAxes)
        ax1.set_title('Bid Strategy vs. P-Level')


    # --- Plot 2: Profit Comparison (One-Price vs Two-Price) ---
    ax2 = axs[0, 1]
    # Safely get profit values using .get() with default NaN
    one_price_profit = results.get('one_price', {}).get('profit', np.nan)
    two_price_profit = results.get('two_price', {}).get('profit', np.nan)
    model_names = ['One-Price', 'Two-Price']
    profits = [one_price_profit, two_price_profit]

    # Filter out NaN values before plotting
    valid_profits = [p for p in profits if not np.isnan(p)]
    valid_names = [name for name, p in zip(model_names, profits) if not np.isnan(p)]

    if valid_profits:
         bars = ax2.bar(valid_names, valid_profits, color=['skyblue', 'lightcoral'])
         ax2.set_ylabel('Total Expected Profit (€)')
         ax2.set_title('Profit Comparison: One-Price vs. Two-Price')
         ax2.grid(axis='y', linestyle='--')
         # Add labels to bars
         ax2.bar_label(bars, fmt='{:,.2f} €')
    else:
         ax2.text(0.5, 0.5, 'Profit Data Missing\nor Invalid', horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes)
         ax2.set_title('Profit Comparison: One-Price vs. Two-Price')


    # --- Plot 3: Bid Comparison (Avg Stochastic vs P90/CVaR) ---
    ax3 = axs[1, 0]
    # Safely get bid values using .get() with default NaN
    avg_bid_one = results.get('one_price', {}).get('avg_bid', np.nan)
    avg_bid_two = results.get('two_price', {}).get('avg_bid', np.nan)
    bid_p90 = results.get('p90', {}).get('also_x_bid', np.nan)
    bid_cvar = results.get('p90', {}).get('cvar_bid', np.nan)

    bid_names = ['Avg One-Price', 'Avg Two-Price', 'P90', 'CVaR']
    bid_values = [avg_bid_one, avg_bid_two, bid_p90, bid_cvar]

    # Filter out NaN values
    valid_bid_values = [b for b in bid_values if not np.isnan(b)]
    valid_bid_names = [name for name, b in zip(bid_names, bid_values) if not np.isnan(b)]

    if valid_bid_values:
         bars = ax3.bar(valid_bid_names, valid_bid_values, color=['lightblue', 'lightgreen', 'gold', 'salmon'])
         ax3.set_ylabel('Bid Amount (kW)')
         ax3.set_title('Comparison of Bidding Strategies')
         ax3.grid(axis='y', linestyle='--')
         ax3.bar_label(bars, fmt='{:,.1f} kW')
    else:
         ax3.text(0.5, 0.5, 'Bid Data Missing\nor Invalid', horizontalalignment='center', verticalalignment='center', transform=ax3.transAxes)
         ax3.set_title('Comparison of Bidding Strategies')


    # --- Plot 4: Distribution of Profits per Scenario ---
    ax4 = axs[1, 1]
    # Safely get scenario profit dictionaries
    profit_scen_one = results.get('one_price', {}).get('profit_per_scenario', {})
    profit_scen_two = results.get('two_price', {}).get('profit_per_scenario', {})

    plotted = False # Flag to check if any histogram was plotted
    if isinstance(profit_scen_one, dict) and profit_scen_one:
         # Filter out potential NaNs before plotting histogram
         valid_profits_one = [p for p in profit_scen_one.values() if not np.isnan(p)]
         if valid_profits_one:
              ax4.hist(valid_profits_one, bins=20, alpha=0.6, label='One-Price Profit Dist.', color='skyblue')
              plotted = True
    if isinstance(profit_scen_two, dict) and profit_scen_two:
         # Filter out potential NaNs
         valid_profits_two = [p for p in profit_scen_two.values() if not np.isnan(p)]
         if valid_profits_two:
              ax4.hist(valid_profits_two, bins=20, alpha=0.6, label='Two-Price Profit Dist.', color='lightcoral')
              plotted = True

    if plotted:
        ax4.set_xlabel('Profit per Scenario (€)')
        ax4.set_ylabel('Frequency (Number of Scenarios)')
        ax4