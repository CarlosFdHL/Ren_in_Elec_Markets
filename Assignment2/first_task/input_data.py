import numpy as np
import pandas as pd
import os
import glob
import itertools
import random
random.seed(5)

class InputData:
    def __init__(self, T:list, W:list, scenario:dict, prob_scenario:float):  
        # SETS
        self.T = T
        self.W = W

        # PARAMETERS
        self.scenario = scenario
        self.p_nom = 500 # MW
        self.prob_scenario = prob_scenario
        self.positiveBalancePriceFactor = 1.25
        self.negativeBalancePriceFactor = 0.85
    
# --------------------------------------------------------------------------------
#       DEFINITION OF SETS
# --------------------------------------------------------------------------------
num_samples = 300  # Adjust this number as needed
max_samples = 11*22*10
T = [i for i in range(1,25)]
W = [i for i in range(1,num_samples+1)]

# --------------------------------------------------------------------------------
#       LOAD DATA FROM FILES AND CREATE SCENARIOS
# --------------------------------------------------------------------------------

# Helper function to load files
def load_files(directory):
    """Loads all files from a given directory."""
    return glob.glob(os.path.join(directory, '*'))

# PATHS
script_dir = os.path.dirname(__file__)
data_dir = os.path.join(script_dir, '../data')

# Define paths for different scenarios
path_rp_29_march = os.path.join(data_dir, 'rate_of_production_scenarios/29march')
path_rp_30_march = os.path.join(data_dir, 'rate_of_production_scenarios/30march')
files_rp_29 = load_files(path_rp_29_march)
files_rp_30 = load_files(path_rp_30_march)

path_eprice = os.path.join(data_dir, 'eprice_scenarios')
files_eprice = load_files(path_eprice)
path_system_cond = os.path.join(data_dir, 'ps_condition/ps_condition_scenarios.csv')


# SCENARIOS
# Rate of production scenarios
rp_scenarios = {}
w_count = 1
for file in files_rp_29:
    data = pd.read_csv(file, sep=';')
    data = dict(zip(T[:], data.iloc[:,4]))
    rp_scenarios[w_count] = data
    w_count += 1
for file in files_rp_30:
    data = pd.read_csv(file, sep=';')
    data = dict(zip(T[:], data.iloc[:,4]))
    rp_scenarios[w_count] = data

    w_count += 1

# System condition scenarios
sc_scenarios = {}
system_condition_scenarios = pd.read_csv(path_system_cond, sep=',')
num_rows = system_condition_scenarios.shape[0]

for i in range(num_rows):
    sc_scenarios[i+1] = {j+1: int(system_condition_scenarios.iloc[i, j]) for j in range(system_condition_scenarios.shape[1])}

# Electricity price scenarios
w_count = 1
eprice_scenarios = {}
for file in files_eprice:
    data = pd.read_csv(os.path.join(path_eprice, file), sep=',', header=None)
    data = dict(zip(T[:], data.iloc[:,1]))
    eprice_scenarios[w_count] = data
    w_count += 1
rp_keys = list(rp_scenarios.keys())
sc_keys = list(sc_scenarios.keys())
eprice_keys = list(eprice_scenarios.keys())
combinations = itertools.product(rp_keys, sc_keys, eprice_keys)

# Total scenarios
scenarios = {}
# for w, (rp_index, sc_index, eprice_index) in zip(W, combinations):
#     scenarios[w] = {
#         'rp': rp_scenarios[rp_index],
#         'sc': sc_scenarios[sc_index],
#         'eprice': eprice_scenarios[eprice_index]
#     }

# List of all combinations
all_combinations = list(itertools.product(rp_keys, sc_keys, eprice_keys))

# Randomly sample num_samples combinations from all_combinations
sampled_combinations = random.sample(all_combinations, num_samples)

# Obtain a random set of num_samples scenarios
scenarios = {i+1: {
    'rp': rp_scenarios[rp_index],
    'sc': sc_scenarios[sc_index],
    'eprice': eprice_scenarios[eprice_index]
} for i, (rp_index, sc_index, eprice_index) in enumerate(sampled_combinations)}

prob_scenario = 1/len(scenarios)  # Probability of each scenario
# --------------------------------------------------------------------------------