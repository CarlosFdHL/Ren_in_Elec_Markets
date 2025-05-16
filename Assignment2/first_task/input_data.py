import numpy as np
import pandas as pd
import os
import glob
import itertools
import random
import matplotlib.pyplot as plt
random.seed(2) #Used seed for results shown in report: 5

class InputData:
    def __init__(self, T:list, W:list, scenario:dict, prob_scenario:float, model_type:str = 'one_price'):  
        # SETS
        self.T = T
        self.W = W

        # PARAMETERS
        self.scenario = scenario
        self.p_nom = 500 # MW
        self.prob_scenario = prob_scenario
        self.positiveBalancePriceFactor = 1.25
        self.negativeBalancePriceFactor = 0.85

        self.model_type = model_type
    
# --------------------------------------------------------------------------------
#       DEFINITION OF SETS
# --------------------------------------------------------------------------------

num_samples = 200  # Adjust this number as needed
cv_nsamples = 1600 # Adjust this number as needed
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
# We don't want negative prices, so we set them to 0, if they exist
for scenario in eprice_scenarios.values():
    for t in scenario:
        if scenario[t] < 0:
            scenario[t] = 0

rp_keys = list(rp_scenarios.keys())
sc_keys = list(sc_scenarios.keys())
eprice_keys = list(eprice_scenarios.keys())
combinations = itertools.product(rp_keys, sc_keys, eprice_keys)

# List of all combinations
all_combinations = list(itertools.product(rp_keys, sc_keys, eprice_keys))

# Randomly sample num_samples combinations from all_combinations
sampled_combinations = random.sample(all_combinations, num_samples)

# Randomly sample combinations for cross-validation
cv_combinations = random.sample(all_combinations, cv_nsamples)

# Obtain a random set of num_samples scenarios
scenarios = {i+1: {
    'rp': rp_scenarios[rp_index],
    'sc': sc_scenarios[sc_index],
    'eprice': eprice_scenarios[eprice_index]
} for i, (rp_index, sc_index, eprice_index) in enumerate(sampled_combinations)}

# Obtain all the scenarios used for the cross validation analysis
cv_scenarios = {i+1: {
    'rp': rp_scenarios[rp_index],
    'sc': sc_scenarios[sc_index],
    'eprice': eprice_scenarios[eprice_index]
} for i, (rp_index, sc_index, eprice_index) in enumerate(cv_combinations)}

prob_scenario = 1/len(scenarios)  # Probability of each scenario

# Ex-post analysis scenarios
expost_combinations = [index for index in all_combinations if index not in sampled_combinations]

# Create a dictionary with the scenarios for the ex-post analysis
expost_scenarios = {i+1: {
    'rp': rp_scenarios[rp_index],
    'sc': sc_scenarios[sc_index],
    'eprice': eprice_scenarios[eprice_index]
} for i, (rp_index, sc_index, eprice_index) in enumerate(expost_combinations)}

W_expost = list(expost_scenarios.keys())

# negative_price_count = 0

# --------------------------------------------------------------------------------