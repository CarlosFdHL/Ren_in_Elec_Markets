import matplotlib.pyplot as plt
import sys
import numpy as np
from .input_data import *
from .model_risk_averse import RiskAverseExPostAnalysis
import time

import matplotlib as mpl
mpl.rcParams.update(mpl.rcParamsDefault)
plt.rcParams['font.family'] = 'serif' 


if __name__ == "__main__":
    start_time = time.time() # Start timer
    if len(sys.argv) != 2:
        raise ValueError("Usage: python main.py [one_price|two_price]")
    
    model_type = sys.argv[1].lower()    
    
    # 1. Create InputData instance
    input_data = InputData(T=T, W=W, scenario=scenarios, prob_scenario=prob_scenario, model_type=model_type)
    
    # 2. Run ExPostAnalysis for different beta values
    # beta_values = np.array([0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.83, 0.85, 0.9, 0.93, 0.95, 0.98, 1])
    beta_values = np.linspace(0, 1, 101)  
    results = []
    
    for beta in beta_values:
        print(f"\nRunning model with beta = {beta:.2f}")
        
        model = RiskAverseExPostAnalysis(
            input_data=input_data,
            beta=beta,
            alpha=0.90,   # CVaR confidence level (as per task)
            verbose=False # Disable detailed logging for batch runs
        )
        model.run()
        
        profit_per_scenario = [model.results.profit_per_scenario[w].getValue()for w in model.data.W]
        power_bidded = [model.results.production[t] for t in model.data.T]
        
        # Store results
        results.append({
            'beta': beta,
            'expected_profit': model.results.total_expected_profit,
            'cvar': model.results.cvar,
            'profit_per_scenario': profit_per_scenario,
            'power_bidded': power_bidded,
            'total_expected_profit': model.results.total_expected_profit,
        })
    
    # 3. Plot Expected Profit vs. CVaR
    plt.figure(figsize=(5, 4))
    plt.plot([res['cvar'] for res in results], [res['expected_profit'] for res in results], '-', markersize=6)

    indices_to_label = [0, len(beta_values)//2, len(beta_values)-1]
    for i in indices_to_label:
        x = results[i]['cvar']
        y = results[i]['expected_profit']
        beta = beta_values[i]
        # plt.text(x, y, f"$\\beta = {beta:.2f}$", fontsize=9, ha='left', va='bottom', alpha=0.8)

    plt.xlabel('Conditional Value at Risk (CVaR)', fontsize=9)
    plt.ylabel('Expected Profit (€)', fontsize=9)
    plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0)) 
    plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0)) 
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    # 4. Plot Profit Volatility vs. Beta

    plt.figure(figsize=(8, 6))
    plt.plot(beta_values, [res['total_expected_profit'] for res in results], '-')
    plt.xlabel('Risk Weight (Beta)')
    plt.ylabel('Total Expected Profit (€)')
    plt.grid(True)
    plt.tight_layout()

    # 5. Plot Profit per Scenario vs Beta
    fig, ax = plt.subplots(1,2,figsize=(12, 3))
    colors = plt.get_cmap('tab10').colors  # 10 colores bien diferenciados
    color_map = {0: colors[0], 0.8: colors[1], 1: colors[2]}
    j = -1
    for i, res in enumerate(results):
        if res['beta'] == 0 or res['beta'] == 1 or res['beta'] == 0.5:
            j += 1
            ax[0].hist(res['profit_per_scenario'], label=f"$\\beta = {res['beta']:.2f}$",
                    bins=30, alpha=0.3, color=colors[j], edgecolor='black')
    ax[0].legend()
    ax[0].grid()
    ax[0].set_xlabel('Profit per Scenario (€)')
    ax[0].set_ylabel('Frequency')
    ax[1].plot(beta_values, [res['total_expected_profit'] for res in results], '-')
    ax[1].set_xlabel('Risk Weight (Beta)')
    ax[1].set_ylabel('Total Expected Profit (€)')
    ax[1].grid()
    ax[1].ticklabel_format(style='sci', axis='y', scilimits=(0,0))  
    plt.tight_layout()


    # Plot bids for different insample sizes with beta = 0.5
    
    beta = 0.5
    sample_sizes = [100, 200, 300, 400, 500]
    bids_dict = {}

    for n in sample_sizes:
        sampled_combinations = random.sample(all_combinations, n)
        scenarios = {i+1: {
            'rp': rp_scenarios[rp_index],
            'sc': sc_scenarios[sc_index],
            'eprice': eprice_scenarios[eprice_index]
        } for i, (rp_index, sc_index, eprice_index) in enumerate(sampled_combinations)}
        
        input_data = InputData(T, list(range(1, n+1)), scenarios, prob_scenario, model_type=model_type)
        model = RiskAverseExPostAnalysis(
            input_data=input_data,
            beta=beta,
            alpha=0.90,   # CVaR confidence level (as per task)
            verbose=False # Disable detailed logging for batch runs
        )
        model.run() 
        bids = [model.results.production[t] for t in model.data.T]       
        bids_dict[n] = bids

    plt.figure(figsize=(10,6))
    colors = plt.get_cmap('tab10').colors 
    markers = ['o', 's', 'D', '^', 'v']
    for idx, (n, bids) in enumerate(bids_dict.items()):
        plt.plot(
            T, bids,
            label=f'In-sample size {n}',
            color=colors[idx % len(colors)],
            linewidth=2.5,
            marker=markers[idx % len(markers)],
            markersize=6,
            alpha=0.85
        )
    plt.xlabel('Hour')
    plt.ylabel('Bid (MW)')
    plt.title(f'Optimal Bids for Different In-sample Sizes (beta={beta})')
    plt.legend()
    plt.grid(True)
    plt.show()
    end_time = time.time()  # End timer
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")