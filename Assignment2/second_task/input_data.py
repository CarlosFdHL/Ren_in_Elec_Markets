import numpy as np
import pandas as pd
import os
import glob
import itertools
import random
random.seed(5) # Use a fixed seed for reproducibility

class InputData:
    def __init__(self, num_samples=200, cv_nsamples=1600): # Allow configuration
        """
        Initializes the InputData class by loading and processing scenario data.

        Args:
            num_samples (int): Number of scenarios for main model training/evaluation.
                               Needs to be >= 2 for P90 model split.
            cv_nsamples (int): Number of scenarios for cross-validation (if used elsewhere).
        """
        if num_samples < 2:
            raise ValueError("num_samples must be at least 2 for P90 split.")

        self.p_nom = 600       # Maximum capacity (kW)
        self.T = list(range(1, 25))   # Time periods (hours 1 to 24)
        self.W = list(range(1, num_samples + 1)) # Scenario indices

        # Default Price Factors (can be overridden externally if needed)
        self.positiveBalancePriceFactor = 0.9  # For upward imbalance compensation
        self.negativeBalancePriceFactor = 1.1  # For downward imbalance penalty

        # --------------------------------------------------------------------------------
        #         LOAD DATA FROM FILES AND CREATE SCENARIOS
        # --------------------------------------------------------------------------------

        # Helper function to load files
        def load_files(directory):
            """Loads all .csv files from a given directory."""
            # Use absolute path for robustness
            abs_directory = os.path.abspath(directory)
            if not os.path.isdir(abs_directory):
                 raise FileNotFoundError(f"Directory not found: {abs_directory}")
            return glob.glob(os.path.join(abs_directory, '*.csv')) # Assume csv

        # PATHS (More robust path handling)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Assume data directory is a sibling to the directory containing this script
        data_dir = os.path.join(script_dir, '../data')

        # Define paths for different scenarios
        path_rp_29_march = os.path.join(data_dir, 'rate_of_production_scenarios/29march')
        path_rp_30_march = os.path.join(data_dir, 'rate_of_production_scenarios/30march')
        path_eprice = os.path.join(data_dir, 'eprice_scenarios')
        path_system_cond = os.path.join(data_dir, 'ps_condition/ps_condition_scenarios.csv')

        try:
            files_rp_29 = load_files(path_rp_29_march)
            files_rp_30 = load_files(path_rp_30_march)
            files_eprice = load_files(path_eprice)

            if not files_rp_29 and not files_rp_30:
                 raise FileNotFoundError("No rate of production scenario files found.")
            if not files_eprice:
                 raise FileNotFoundError("No electricity price scenario files found.")
            if not os.path.exists(path_system_cond):
                 raise FileNotFoundError(f"System condition file not found: {path_system_cond}")

            # SCENARIOS
            # Rate of production scenarios
            rp_scenarios = {}
            w_count = 1
            # Consistent handling assuming header and specific column index
            for file in files_rp_29 + files_rp_30:
                data = pd.read_csv(file, sep=';')
                # Ensure data aligns with self.T (hours 1-24)
                if len(data) >= len(self.T):
                     # Assuming column 4 holds the rate for hours 1-24
                    rp_scenarios[w_count] = dict(zip(self.T, data.iloc[:len(self.T), 4]))
                    w_count += 1
                else:
                    print(f"Warning: Skipping file {file} due to insufficient data rows.")


            # System condition scenarios
            sc_scenarios = {}
            system_condition_scenarios = pd.read_csv(path_system_cond, sep=',')
            num_rows_sc = system_condition_scenarios.shape[0]
            # Ensure data aligns with self.T (hours 1-24)
            if system_condition_scenarios.shape[1] >= len(self.T):
                for i in range(num_rows_sc):
                     # Assuming columns 0 to 23 correspond to hours 1 to 24
                    sc_scenarios[i+1] = {t: int(system_condition_scenarios.iloc[i, t-1]) for t in self.T}
            else:
                 raise ValueError("System condition file has fewer columns than hours in T.")


            # Electricity price scenarios
            eprice_scenarios = {}
            w_count = 1
            for file in files_eprice:
                # Assuming no header and column 1 holds the price
                data = pd.read_csv(file, sep=',', header=None)
                 # Ensure data aligns with self.T (hours 1-24)
                if len(data) >= len(self.T):
                    eprice_scenarios[w_count] = dict(zip(self.T, data.iloc[:len(self.T), 1]))
                    w_count += 1
                else:
                     print(f"Warning: Skipping file {file} due to insufficient data rows.")


            # Combine scenarios
            rp_keys = list(rp_scenarios.keys())
            sc_keys = list(sc_scenarios.keys())
            eprice_keys = list(eprice_scenarios.keys())

            if not rp_keys or not sc_keys or not eprice_keys:
                raise ValueError("Failed to load scenarios for rp, sc, or eprice.")

            all_combinations = list(itertools.product(rp_keys, sc_keys, eprice_keys))
            max_possible_samples = len(all_combinations)

            print(f"Total possible unique scenario combinations: {max_possible_samples}")

            # Adjust sample sizes if necessary
            if num_samples > max_possible_samples:
                print(f"Warning: Requested num_samples ({num_samples}) > available ({max_possible_samples}). Using {max_possible_samples}.")
                num_samples = max_possible_samples
                self.W = list(range(1, num_samples + 1)) # Update W list

            if cv_nsamples > max_possible_samples:
                print(f"Warning: Requested cv_nsamples ({cv_nsamples}) > available ({max_possible_samples}). Using {max_possible_samples}.")
                cv_nsamples = max_possible_samples

            # Ensure enough samples for potential later split if needed
            if num_samples + cv_nsamples > max_possible_samples:
                 # Prioritize num_samples, reduce cv_nsamples if overlap needed
                 available_for_cv = max_possible_samples
                 # Or sample them independently allowing overlap:
                 print(f"Warning: num_samples + cv_nsamples > total combinations. Samples might overlap or be reduced.")


            # Randomly sample num_samples combinations from all_combinations
            sampled_combinations = random.sample(all_combinations, num_samples)

            # Randomly sample combinations for cross-validation (can overlap with main samples)
            cv_combinations = random.sample(all_combinations, cv_nsamples)

            # Obtain the main set of num_samples scenarios
            self.scenarios = {i + 1: {
                'rp': rp_scenarios[rp_index],
                'sc': sc_scenarios[sc_index],
                'eprice': eprice_scenarios[eprice_index]
            } for i, (rp_index, sc_index, eprice_index) in enumerate(sampled_combinations)}

            # Obtain the scenarios used for the cross validation analysis
            self.cv_scenarios = {i + 1: {
                'rp': rp_scenarios[rp_index],
                'sc': sc_scenarios[sc_index],
                'eprice': eprice_scenarios[eprice_index]
            } for i, (rp_index, sc_index, eprice_index) in enumerate(cv_combinations)}

            # Calculate probability assuming equal likelihood for sampled scenarios
            self.prob_scenario = 1.0 / len(self.scenarios) if self.scenarios else 0

            # Ex-post analysis scenarios (optional, can be generated if needed)
            # expost_combinations = [index for index in all_combinations if index not in sampled_combinations]
            # self.expost_scenarios = {i+1: { ... } for i, (...) in enumerate(expost_combinations)}
            # self.W_expost = list(self.expost_scenarios.keys())

        except FileNotFoundError as e:
            print(f"Error loading data: {e}")
            # Handle error appropriately, maybe exit or set scenarios to empty
            self.scenarios = {}
            self.cv_scenarios = {}
            self.prob_scenario = 0
            self.W = []
        except ValueError as e:
            print(f"Error processing data: {e}")
            self.scenarios = {}
            self.cv_scenarios = {}
            self.prob_scenario = 0
            self.W = []
        except Exception as e: # Catch other potential errors during loading/processing
             print(f"An unexpected error occurred during data loading: {e}")
             self.scenarios = {}
             self.cv_scenarios = {}
             self.prob_scenario = 0
             self.W = []