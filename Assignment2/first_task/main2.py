import matplotlib.pyplot as plt
import sys
import numpy as np
from .input_data import *
from .risk_analysis import RiskAverseExPostAnalysis

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Usage: python main.py [one_price|two_price]")
    
    model_type = sys.argv[1].lower()    
    
    # 1. Create InputData instance
    input_data = InputData(T=T, W=W, scenario=scenarios, prob_scenario=prob_scenario, model_type=model_type)
    
    # 2. Run ExPostAnalysis for different beta values
    beta_values = np.linspace(0, 1, 30) 
    results = []
    
    for beta in beta_values:
        print(f"\nRunning model with beta = {beta:.2f}")
        
        model = RiskAverseExPostAnalysis(
            input_data=input_data,
            beta=beta,
            alpha=0.90,  # CVaR confidence level (as per task)
            verbose=False # Disable detailed logging for batch runs
        )
        
        model.build_model()
        model.run()
        
        # Store results
        results.append({
            'beta': beta,
            'expected_profit': model.results.total_expected_profit,
            'cvar': model.results.cvar,
            'profit_volatility': np.std([model.results.profit_per_scenario[w].getValue() for w in W])
        })
    
    # 3. Plot Expected Profit vs. CVaR
    plt.figure(figsize=(8, 6))
    plt.plot([res['cvar'] for res in results], [res['expected_profit'] for res in results], 'o-')
    plt.xlabel('Conditional Value at Risk (CVaR)')
    plt.ylabel('Expected Profit (€)')
    plt.title(f'Risk-Averse Offering Strategy ({model_type} scheme)')
    plt.grid(True)
    plt.savefig(f'first_task/output/figures/profit_vs_cvar_{model_type}.png')
    plt.tight_layout()

    # 4. Plot Profit Volatility vs. Beta
    plt.figure(figsize=(8, 6))
    plt.plot(beta_values, [res['profit_volatility'] for res in results], 'o-')
    plt.xlabel('Risk Weight (Beta)')
    plt.ylabel('Profit Volatility (Standard Deviation)')
    plt.title(f'Profit Volatility vs. Risk Aversion ({model_type} scheme)')
    plt.grid(True)
    plt.savefig(f'first_task/output/figures/volatility_vs_beta_{model_type}.png')
    plt.tight_layout()
    plt.show()