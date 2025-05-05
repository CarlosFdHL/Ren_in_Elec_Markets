# model_p90_bidding.py
import numpy as np
import pandas as pd
from gurobipy import GRB

class P90BiddingModel:
    def __init__(self, input_data, verbose=True):
        self.data = input_data
        self.verbose = verbose
        self.results = type('', (), {})()  # Simple results container
        
        # Split scenarios into in-sample (100) and out-sample (200)
        self.in_sample_scenarios = {k: input_data.scenarios[k] for k in list(input_data.scenarios.keys())[:100]}
        self.out_sample_scenarios = {k: input_data.scenarios[k] for k in list(input_data.scenarios.keys())[100:]}
        
    def calculate_max_loads(self, scenarios):
        """Calculate maximum load for each scenario"""
        max_loads = []
        for w, scenario in scenarios.items():
            max_load = max(scenario['rp'][t] * self.data.p_nom for t in self.data.T)
            max_loads.append(max_load)
        return np.array(max_loads)
    
    def calculate_bids(self):
        """Task 2.1 - Calculate ALSO-X and CVaR bids"""
        max_loads = self.calculate_max_loads(self.in_sample_scenarios)
        
        # ALSO-X (P90)
        self.results.also_x_bid = np.percentile(max_loads, 90)
        
        # CVaR (Average of worst 10%)
        sorted_loads = np.sort(max_loads)
        self.results.cvar_bid = np.mean(sorted_loads[-10:])  # Exactly 10 worst cases (10% of 100)
        
        if self.verbose:
            print(f"\nALSO-X (P90) Bid: {self.results.also_x_bid:.2f} kW")
            print(f"CVaR Bid: {self.results.cvar_bid:.2f} kW")
    
    def verify_bids(self):
        """Task 2.2 - Out-of-sample verification"""
        test_max_loads = self.calculate_max_loads(self.out_sample_scenarios)
        
        self.results.also_x_shortfalls = np.maximum(test_max_loads - self.results.also_x_bid, 0)
        self.results.cvar_shortfalls = np.maximum(test_max_loads - self.results.cvar_bid, 0)
        
        self.results.also_x_success = 100 * np.mean(self.results.also_x_shortfalls == 0)
        self.results.cvar_success = 100 * np.mean(self.results.cvar_shortfalls == 0)
        
        if self.verbose:
            print("\nOut-of-sample Verification:")
            print(f"ALSO-X Success Rate: {self.results.also_x_success:.1f}%")
            print(f"CVaR Success Rate: {self.results.cvar_success:.1f}%")
    
    def p_requirement_analysis(self):
        """Task 2.3 - P requirement sensitivity"""
        p_values = range(80, 101, 5)
        max_loads = self.calculate_max_loads(self.in_sample_scenarios)
        
        analysis = []
        for p in p_values:
            bid = np.percentile(max_loads, p)
            test_loads = self.calculate_max_loads(self.out_sample_scenarios)
            shortfalls = np.maximum(test_loads - bid, 0)
            success_rate = 100 * np.mean(shortfalls == 0)
            avg_shortfall = np.mean(shortfalls[shortfalls > 0]) if np.any(shortfalls > 0) else 0
            
            analysis.append({
                'P': p,
                'bid': bid,
                'success_rate': success_rate,
                'avg_shortfall': avg_shortfall,
                'expected_shortfall': (100 - success_rate) * avg_shortfall / 100
            })
        
        self.results.p_analysis = pd.DataFrame(analysis)
        
        if self.verbose:
            print("\nP Requirement Analysis:")
            print(self.results.p_analysis.to_string(index=False))
    
    def run(self):
        self.calculate_bids()
        self.verify_bids()
        self.p_requirement_analysis()