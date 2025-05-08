import matplotlib.pyplot as plt
import sys
from input_data import InputData
from expost_analysis import ExPostAnalysis

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Usage: python main.py [one_price|two_price]")
    
    model_type = sys.argv[1].lower()
    
    # 1. Define your input data parameters
    T = list(range(24))  # 24 hours
    W = list(range(10))  # 10 scenarios
    prob_scenario = 1/len(W)  # Equal probability
    
    # Create scenario data - this must match what your InputData expects
    scenarios = {
        w: {
            'eprice': {t: 50 + w + t for t in T},  # Example price data
            'rp': {t: 0.9 + 0.01 * ((t + w) % 10) for t in T},  # Production factor
            'sc': {t: (t + w) % 2 for t in T},  # System condition
        }
        for w in W
    }
    
    # 2. Create InputData instance
    input_data = InputData(T=T, W=W, scenarios=scenarios, prob_scenario=prob_scenario)
    input_data.model_type = model_type
    input_data.p_nom = 100  # Nominal power
    input_data.positiveBalancePriceFactor = 0.9
    input_data.negativeBalancePriceFactor = 0.8
    
    # 3. Run ExPostAnalysis
    model = ExPostAnalysis(
        input_data=input_data,
        beta=0.2,  # Risk weight
        alpha=0.90,  # CVaR confidence
        verbose=True
    )
    
    model.build_model()
    model.run()
    model.print_results()
    model.plot()
    
    plt.show()
    print("\nAnalysis complete\n")