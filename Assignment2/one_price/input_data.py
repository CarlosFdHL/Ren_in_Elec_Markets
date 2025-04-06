import numpy as np
import pandas as pd
import os
import glob
import itertools
import random

class InputData:
    def __init__(self, generators: list, bid_offers: dict, demand: list, demand_per_load: dict):  
        # Initialize dictionaries to store data

        # SETS 
        self.generators = [i for i in range(1,len(generators)+1)]
        self.timeSpan = [i for i in range(1,2)]
        self.loads = [i for i in range(1,len(demand_per_load)+1)]

        # GENERATOR DATA
        self.Pmax = {}
        self.Pmin = {}
        self.Max_up_reserve = {}
        self.Max_down_reserve = {}
        self.UT = {}
        self.DT = {}
        self.RU = {}
        self.RD = {}
        self.wind = {}

        # BID OFFERS
        self.bid_offers = bid_offers
        self.demand = demand
        self.demand_bid_price = [] 
        self.demand_per_load = demand_per_load

        # Adjust demand to the time span
        num_hours = len(self.timeSpan)
        num_days = num_hours // 24
        if num_hours <= 24:
            factor = 24 / num_hours
            adjusted_demand = [self.demand[int(i * factor)] for i in range(num_hours)]
        else:
            adjusted_demand = [self.demand[i % 24] for i in range(num_hours)]
        self.demand = adjusted_demand

        # Populate the dictionaries with data from the generators input
        for gen in generators:
            unit_id = gen['Unit #']
            self.Pmax[unit_id] = gen['Pmax (MW)']
            self.Pmin[unit_id] = gen['Pmin (MW)']
            self.Max_up_reserve[unit_id] = gen['R+ (MW)']
            self.Max_down_reserve[unit_id] = gen['R- (MW)']
            self.UT[unit_id] = gen['UT (h)']
            self.DT[unit_id] = gen['DT (h)']
            self.RU[unit_id] = gen['RU (MW/h)']
            self.RD[unit_id] = gen['RD (MW/h)']
            self.wind[unit_id] = gen['wind']
        
        # CALCULATE DEMAND BID PRICE
        sorted_keys = sorted(bid_offers, key=lambda k: bid_offers[k])
        sorted_power = []
        
        for t, _ in enumerate(self.timeSpan):
            demand_bid_price = {}
            for key in sorted_keys:  
                if not self.wind[key]:
                    sorted_power.append(self.Pmax[key])
                else:
                    sorted_power.append(self.Pmax[key][t - 24 * num_days])
            accumulated_power = 0
            for key, power in zip(sorted_keys, sorted_power):
                accumulated_power += power
                if accumulated_power >= self.demand[t]:
                    last_bid_demand = self.bid_offers[key]
                    break
            first_bid_demand = 10 * last_bid_demand
            exponential_increment = np.log(first_bid_demand/last_bid_demand) / (len(demand_per_load) - 1)
            for i, (key, load) in enumerate(demand_per_load.items()):
                demand_bid_price[key] = last_bid_demand * np.exp(exponential_increment * i)
            self.demand_bid_price.append(demand_bid_price)

T = [i for i in range(1,25)]
W = [i for i in range(1,11*22*10+1)]
print(T)
# --------------------------------------------------------------------------------
#       LOAD DATA FROM FILES
# --------------------------------------------------------------------------------

# PATHS
script_dir = os.path.dirname(__file__)
data_dir = os.path.join(script_dir, '../data')

# Define paths for different scenarios
path_rp_29_march = os.path.join(data_dir, 'rate_of_production_scenarios/29march')
path_rp_30_march = os.path.join(data_dir, 'rate_of_production_scenarios/30march')
path_eprice = os.path.join(data_dir, 'eprice_scenarios')
files_eprice = os.listdir(path_eprice)
path_system_cond = os.path.join(data_dir, 'ps_condition/ps_condition_scenarios.csv')

# Helper function to load files
def load_files(directory):
    """Carga todos los archivos de un directorio dado"""
    return glob.glob(os.path.join(directory, '*'))

# Load files
files_rp_29 = load_files(path_rp_29_march)
files_rp_30 = load_files(path_rp_30_march)

rp_scenarios = {}
w_count = 1
for file in files_rp_29:
    data = pd.read_csv(file, sep=';')
    data = dict(zip(T[:], data.iloc[:,2]))
    rp_scenarios[w_count] = data
    w_count += 1
for file in files_rp_30:
    data = pd.read_csv(file, sep=';')
    data = dict(zip(T[:], data.iloc[:,2]))
    rp_scenarios[w_count] = data
    w_count += 1

# System condition scenarios
sc_scenarios = {}
system_condition_scenarios = pd.read_csv(path_system_cond, sep=',')
num_rows = system_condition_scenarios.shape[0]

for i in range(num_rows):
    sc_scenarios[i+1] = system_condition_scenarios.loc[i].to_list()

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

scenarios = {}
for w, (rp_index, sc_index, eprice_index) in zip(W, combinations):
    scenarios[w] = {
        'rp': rp_scenarios[rp_index],
        'sc': sc_scenarios[sc_index],
        'eprice': eprice_scenarios[eprice_index]
    }

# List of all combinations
all_combinations = list(itertools.product(rp_keys, sc_keys, eprice_keys))

# Randomly sample num_samples combinations from all_combinations
num_samples = 2420  # el número total que mencionaste
sampled_combinations = random.sample(all_combinations, num_samples)

# Obtain a random set of num_samples scenarios
scenarios = {i+1: {
    'rp': rp_scenarios[rp_index],
    'sc': sc_scenarios[sc_index],
    'eprice': eprice_scenarios[eprice_index]
} for i, (rp_index, sc_index, eprice_index) in enumerate(sampled_combinations)}

