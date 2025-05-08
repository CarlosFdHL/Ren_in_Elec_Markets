import matplotlib.pyplot as plt
import sys
import numpy as np
from input_data import InputData
from risk_analysis import ExPostAnalysis

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Usage: python main.py [one_price|two_price]")
    
    model_type = sys.argv[1].lower()
    
    # 1. Define input data parameters
    T = list(range(24))  # 24 hours
    W = list(range(20))  # 10 scenarios
    prob_scenario = 1 / len(W)  # Equal probability
    
    # Create scenario data
    scenarios = {
        w: {
            'eprice': {t: 50 + w + t for t in T},  # Example price data
            'rp': {t: 0.9 + 0.01 * ((t + w) % 10) for t in T},  # Production factor
            'sc': {t: (t + w) % 2 for t in T},  # System condition
        }
        for w in W
    }
    
    # 2. Create InputData instance
    input_data = InputData(T=T, W=W, scenario=scenarios, prob_scenario=prob_scenario)
    input_data.model_type = model_type
    input_data.p_nom = 100  # Nominal power
    input_data.positiveBalancePriceFactor = 0.9
    input_data.negativeBalancePriceFactor = 0.8
    
    # 3. Run ExPostAnalysis for different beta values
    beta_values = np.linspace(0, 1, 11)  # [0.0, 0.1, ..., 1.0]
    results = []
    
    for beta in beta_values:
        print(f"\nRunning model with beta = {beta:.1f}")
        
        model = ExPostAnalysis(
            input_data=input_data,
            beta=beta,
            alpha=0.90,  # CVaR confidence level (as per task)
            verbose=True # Disable detailed logging for batch runs
        )
        
        model.build_model()
        model.run()
        
        # Store results
        results.append({
            'beta': beta,
            'expected_profit': model.results.profit,
            'cvar': model.objective_cvar.getValue(),
            'profit_volatility': np.std([model.results.profit_per_scenario[w].getValue() for w in W])
        })
    
    # 4. Plot Expected Profit vs. CVaR
    plt.figure(figsize=(8, 6))
    plt.plot([res['cvar'] for res in results], [res['expected_profit'] for res in results], 'o-')
    plt.xlabel('Conditional Value at Risk (CVaR)')
    plt.ylabel('Expected Profit (€)')
    plt.title(f'Risk-Averse Offering Strategy ({model_type} scheme)')
    plt.grid(True)
    plt.savefig(f'profit_vs_cvar_{model_type}.png')
    plt.show()
    
    # 5. Plot Profit Volatility vs. Beta
    plt.figure(figsize=(8, 6))
    plt.plot(beta_values, [res['profit_volatility'] for res in results], 'o-')
    plt.xlabel('Risk Weight (Beta)')
    plt.ylabel('Profit Volatility (Standard Deviation)')
    plt.title(f'Profit Volatility vs. Risk Aversion ({model_type} scheme)')
    plt.grid(True)
    plt.savefig(f'volatility_vs_beta_{model_type}.png')
    plt.show()