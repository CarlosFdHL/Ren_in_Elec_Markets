import numpy as np
import pandas as pd
from typing import Dict, List
from input_data import InputData # Assuming input_data.py is available

class P90BiddingModel:
    def __init__(self, input_data: InputData, verbose: bool = True):
        """
        Initialize P90 bidding model.

        Args:
            input_data: InputData class instance containing scenarios and parameters.
            verbose: Whether to print progress messages.
        """
        if not isinstance(input_data, InputData):
            raise TypeError("input_data must be an instance of InputData class")
        if not input_data.scenarios:
             raise ValueError("InputData instance does not contain scenarios.")
        if len(input_data.W) < 2:
             raise ValueError("Need at least 2 scenarios in InputData for train/test split.")


        self.data = input_data
        self.verbose = verbose
        self.results = {} # Initialize results as an empty dictionary

        # Validate essential input
        if not hasattr(self.data, 'p_nom'):
            raise AttributeError("InputData must have 'p_nom' attribute")
        if not hasattr(self.data, 'T'):
            raise AttributeError("InputData must have 'T' attribute")

        # Split scenarios: Use first half for training (in-sample), second half for testing (out-sample)
        # This avoids assuming a fixed number like 100/200 and adapts to num_samples
        all_scenario_keys = sorted(list(self.data.scenarios.keys())) # Sort keys for consistency
        split_index = len(all_scenario_keys) // 2
        if split_index == 0: # Handle case with only 1 sample (though prevented by initial check)
            split_index = 1

        in_sample_keys = all_scenario_keys[:split_index]
        out_sample_keys = all_scenario_keys[split_index:]

        self.in_sample_scenarios = {k: self.data.scenarios[k] for k in in_sample_keys}
        self.out_sample_scenarios = {k: self.data.scenarios[k] for k in out_sample_keys}

        if self.verbose:
             print(f"P90 Model: Using {len(self.in_sample_scenarios)} scenarios for in-sample analysis.")
             print(f"P90 Model: Using {len(self.out_sample_scenarios)} scenarios for out-of-sample verification.")

        if not self.in_sample_scenarios or not self.out_sample_scenarios:
             raise ValueError("Could not create non-empty in-sample and out-sample sets.")


    def _get_hourly_loads(self, scenarios: Dict) -> Dict[int, np.ndarray]:
        """Calculate hourly loads across all provided scenarios."""
        hourly_loads = {t: [] for t in self.data.T}
        for s in scenarios.values():
            for t in self.data.T:
                # Ensure rate ('rp') and price ('eprice') exist for the hour t
                if t in s.get('rp', {}):
                    hourly_loads[t].append(s['rp'][t] * self.data.p_nom)
                else:
                    # Handle missing data for hour t if necessary, e.g., skip or use default
                     print(f"Warning: Missing rate of production data for hour {t} in a scenario.")
                     # Decide how to handle: append NaN, 0, or skip scenario? Appending NaN for now.
                     hourly_loads[t].append(np.nan)

        # Convert lists to numpy arrays, handling potential NaNs
        for t in self.data.T:
             hourly_loads[t] = np.array(hourly_loads[t])

        return hourly_loads


    def _get_max_load_per_scenario(self, scenarios: Dict) -> np.ndarray:
        """Calculate the maximum hourly load for each individual scenario."""
        max_loads = []
        for s in scenarios.values():
             hourly_loads_scenario = [s['rp'].get(t, 0) * self.data.p_nom for t in self.data.T] # Use get with default 0 if hour missing
             max_loads.append(max(hourly_loads_scenario) if hourly_loads_scenario else 0)
        return np.array(max_loads)


    def calculate_bids(self) -> None:
        """Task 2.1: Calculate ALSO-X (P90) and CVaR bids based on in-sample max loads."""
        # We need the maximum load observed within EACH scenario in the training set
        max_loads_in_sample = self._get_max_load_per_scenario(self.in_sample_scenarios)

        if len(max_loads_in_sample) == 0:
            print("Warning: No in-sample data available to calculate bids.")
            self.results['also_x_bid'] = np.nan # Use dict key assignment
            self.results['cvar_bid'] = np.nan   # Use dict key assignment
            return

        # ALSO-X (P90): 90th percentile of the per-scenario maximum loads
        self.results['also_x_bid'] = np.percentile(max_loads_in_sample, 90) # Use dict key assignment

        # CVaR (Conditional Value at Risk - e.g., average of the worst 10% cases)
        # Calculate the threshold for the worst 10% (90th percentile)
        var_90 = np.percentile(max_loads_in_sample, 90)
        # Calculate the mean of loads exceeding or equal to this threshold
        worst_cases = max_loads_in_sample[max_loads_in_sample >= var_90]
        self.results['cvar_bid'] = np.mean(worst_cases) if len(worst_cases) > 0 else var_90 # Use dict key assignment

        if self.verbose:
            print(f"\nP90 Bidding Results (based on {len(max_loads_in_sample)} in-sample scenarios):")
            # Access using dictionary keys
            print(f"ALSO-X (P90) Bid: {self.results['also_x_bid']:.2f} kW")
            print(f"CVaR (Exp. Shortfall at 90%) Bid: {self.results['cvar_bid']:.2f} kW ({(self.results['cvar_bid']/self.data.p_nom*100):.1f}% of p_nom)")

    def verify_bids(self) -> None:
        """Task 2.2: Out-of-sample verification using the calculated bids."""
        # Access using dictionary keys, provide default NaN if key missing
        also_x_bid = self.results.get('also_x_bid', np.nan)
        cvar_bid = self.results.get('cvar_bid', np.nan)

        if np.isnan(also_x_bid) or np.isnan(cvar_bid):
            print("Warning: Bids were not calculated. Skipping verification.")
            # Use dictionary assignment
            self.results['also_x_verification'] = {'success_rate': np.nan, 'avg_shortfall_if_fail': np.nan, 'expected_shortfall': np.nan}
            self.results['cvar_verification'] = {'success_rate': np.nan, 'avg_shortfall_if_fail': np.nan, 'expected_shortfall': np.nan}
            return

        # Get the maximum load observed within EACH scenario in the test set
        max_loads_out_sample = self._get_max_load_per_scenario(self.out_sample_scenarios)

        if len(max_loads_out_sample) == 0:
             print("Warning: No out-of-sample data for verification.")
             # Use dictionary assignment
             self.results['also_x_verification'] = {'success_rate': np.nan, 'avg_shortfall_if_fail': np.nan, 'expected_shortfall': np.nan}
             self.results['cvar_verification'] = {'success_rate': np.nan, 'avg_shortfall_if_fail': np.nan, 'expected_shortfall': np.nan}
             return


        # --- Verification for ALSO-X Bid ---
        shortfalls_also_x = np.maximum(max_loads_out_sample - also_x_bid, 0)
        failures_also_x = shortfalls_also_x > 0
        success_rate_also_x = np.mean(~failures_also_x) * 100
        # Average shortfall ONLY in cases where the bid failed
        avg_shortfall_if_fail_also_x = np.mean(shortfalls_also_x[failures_also_x]) if np.any(failures_also_x) else 0
        # Expected shortfall across ALL out-of-sample scenarios
        expected_shortfall_also_x = np.mean(shortfalls_also_x)

        # Use dictionary assignment
        self.results['also_x_verification'] = {
            'shortfalls': shortfalls_also_x,
            'success_rate': success_rate_also_x,
            'avg_shortfall_if_fail': avg_shortfall_if_fail_also_x,
            'expected_shortfall': expected_shortfall_also_x
        }

        # --- Verification for CVaR Bid ---
        shortfalls_cvar = np.maximum(max_loads_out_sample - cvar_bid, 0)
        failures_cvar = shortfalls_cvar > 0
        success_rate_cvar = np.mean(~failures_cvar) * 100
        avg_shortfall_if_fail_cvar = np.mean(shortfalls_cvar[failures_cvar]) if np.any(failures_cvar) else 0
        expected_shortfall_cvar = np.mean(shortfalls_cvar)

        # Use dictionary assignment
        self.results['cvar_verification'] = {
            'shortfalls': shortfalls_cvar,
            'success_rate': success_rate_cvar,
            'avg_shortfall_if_fail': avg_shortfall_if_fail_cvar,
            'expected_shortfall': expected_shortfall_cvar
        }

        if self.verbose:
            # Access verification results using dictionary keys
            print(f"\nOut-of-Sample Verification ({len(max_loads_out_sample)} scenarios):")
            print("----------------------------------------- | ALSO-X (P90) | CVaR Bid")
            print(f"Success Rate (% scenarios covered)        | {self.results['also_x_verification']['success_rate']:^12.1f} | {self.results['cvar_verification']['success_rate']:^10.1f}")
            print(f"Avg Shortfall WHEN bid fails (kW)       | {self.results['also_x_verification']['avg_shortfall_if_fail']:^12.2f} | {self.results['cvar_verification']['avg_shortfall_if_fail']:^10.2f}")
            print(f"Expected Shortfall across ALL tests (kW)  | {self.results['also_x_verification']['expected_shortfall']:^12.2f} | {self.results['cvar_verification']['expected_shortfall']:^10.2f}")


    def analyze_p_requirements(self, p_values: List[int] = list(range(80, 100, 5)) + [99]) -> None:
        """Task 2.3: P requirement sensitivity analysis using percentiles."""
        # Use in-sample data to determine bids for different P levels
        max_loads_in_sample = self._get_max_load_per_scenario(self.in_sample_scenarios)
        # Use out-of-sample data to test these bids
        max_loads_out_sample = self._get_max_load_per_scenario(self.out_sample_scenarios)

        if len(max_loads_in_sample) == 0 or len(max_loads_out_sample) == 0:
             print("Warning: Insufficient data for P requirement analysis.")
             # Use dictionary assignment
             self.results['p_analysis'] = pd.DataFrame() # Empty DataFrame
             return

        analysis_results = []
        for p in p_values:
            # Calculate bid based on P-th percentile of in-sample max loads
            bid_p = np.percentile(max_loads_in_sample, p)

            # Test this bid against out-of-sample max loads
            shortfalls_p = np.maximum(max_loads_out_sample - bid_p, 0)
            failures_p = shortfalls_p > 0
            success_rate_p = np.mean(~failures_p) * 100
            avg_shortfall_if_fail_p = np.mean(shortfalls_p[failures_p]) if np.any(failures_p) else 0
            expected_shortfall_p = np.mean(shortfalls_p)

            analysis_results.append({
                'P_level': p,
                'bid_kW': bid_p,
                'out_sample_success_rate_perc': success_rate_p,
                'out_sample_avg_shortfall_if_fail_kW': avg_shortfall_if_fail_p,
                'out_sample_expected_shortfall_kW': expected_shortfall_p
            })

        # Assign the DataFrame using dictionary key
        self.results['p_analysis'] = pd.DataFrame(analysis_results) # Use dict key assignment

        if self.verbose:
            print("\nP-Level Requirement Analysis (Out-of-Sample Performance):")
            # Adjust display options for pandas
            with pd.option_context('display.max_rows', None,
                                   'display.max_columns', None,
                                   'display.precision', 2,
                                   'display.width', 100):
                 # Access p_analysis using dictionary key
                 print(self.results['p_analysis'].to_string(index=False))


    def run(self):
        """Execute the complete P90 analysis pipeline."""
        if self.verbose:
             print("\n" + "="*50)
             print("STARTING P90 BIDDING ANALYSIS".center(50))
             print("="*50)

        self.calculate_bids()
        self.verify_bids()
        self.analyze_p_requirements()

        # Add a summary dictionary using dictionary keys
        if 'also_x_bid' in self.results: # Check if key exists
            # Use dictionary assignment
            self.results['summary'] = {
                'p90_bid_kW': self.results.get('also_x_bid', np.nan),
                'cvar_bid_kW': self.results.get('cvar_bid', np.nan),
                # Use .get() chaining for nested dictionaries
                'p90_out_sample_success_rate': self.results.get('also_x_verification', {}).get('success_rate', np.nan),
                'p90_out_sample_expected_shortfall': self.results.get('also_x_verification', {}).get('expected_shortfall', np.nan)
            }
        else:
             # Use dictionary assignment
             self.results['summary'] = {}

        if self.verbose:
             print("\n" + "="*50)
             print("P90 BIDDING ANALYSIS COMPLETE".center(50))
             print("="*50)