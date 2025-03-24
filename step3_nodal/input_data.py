import numpy as np
import pandas as pd
import os
# Description: This file contains the InputData class that is used to store the technical data for each generator and the system demand data.

# The class is used to instantiate an object that is passed to the model class to build the optimization model.
class InputData:
    def __init__(self, generators: list, bid_offers: dict, demand: list, demand_per_load: dict, bus_reactance: dict, bus_capacity: dict):  
        # Initialize dictionaries to store the technical data for each generator
        
        # SETS
        self.generators = [i for i in range(1,len(generators)+1)]
        self.timeSpan = [i for i in range(1,2)]
        self.loads = [i for i in range(1,len(demand_per_load)+1)]
        self.nodes = [i for i in range(1,25)]

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
        self.P_node = {} # Store the node of each generator

        # BID OFFERS
        self.bid_offers = bid_offers
        self.demand = demand
        self.demand_bid_price = [] 
        self.demand_per_load = demand_per_load


        self.bus_reactance = bus_reactance
        self.bus_capacity = bus_capacity

        #Adjust demand to the time span
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
            self.P_node[unit_id] = gen['Node']
        
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
            for i, ((key, _), load) in enumerate(demand_per_load.items()):
                demand_bid_price[key] = last_bid_demand * np.exp(exponential_increment * i)
            self.demand_bid_price.append(demand_bid_price)

# --------------------------------------------------------------------------------
#       LOAD DATA FROM FILES
# --------------------------------------------------------------------------------

# PATHS
script_dir = os.path.dirname(__file__)
wind_cf_path = os.path.join(script_dir, '../data/wind_capacity_factors.csv')
generatorData_path = os.path.join(script_dir, '../data/GeneratorData.csv')
bid_offers_path = os.path.join(script_dir, '../data/bid_offers.csv')
system_demand_path = os.path.join(script_dir, '../data/system_demand.csv')
demand_per_load_path = os.path.join(script_dir, '../data/demand_per_load.csv')
bus_reactance_path = os.path.join(script_dir, '../data/bus_reactance.csv')
bus_capacity_path = os.path.join(script_dir, '../data/bus_capacity.csv')

# WIND FARM CAPACITY FACTORS
wind_farm_capacity = 200
wind_CF = pd.read_csv(wind_cf_path)['wind_cf'].tolist()
wind_CF = [cf * wind_farm_capacity for cf in wind_CF]

# GENERATORS
dtype_dict = {
    'Node': int, 'Pmax (MW)': object, 'Pmin (MW)': float, 'R+ (MW)': float, 'R- (MW)': float,
    'RU (MW/h)': float, 'RD (MW/h)': float, 'UT (h)': int, 'DT (h)': int
}
generators = pd.read_csv(generatorData_path, dtype=dtype_dict)

for index, row in generators.iterrows():
    if row['wind']:
        generators.at[index, 'Pmax (MW)'] = wind_CF.copy() # Assign the wind capacity factors
    else:
        generators.at[index, 'Pmax (MW)'] = float(row['Pmax (MW)']) # Convert to float

generators = generators.to_dict(orient='records') # Convert to list of dictionaries

# GENERATOR BID OFFERS
bid_offers = pd.read_csv(bid_offers_path)
bid_offers = pd.Series(bid_offers.Bid.values, index=bid_offers.Unit).to_dict()

# SYSTEM DEMAND
system_demand = pd.read_csv(system_demand_path)
system_demand = system_demand['Demand'].tolist()

# DEMAND PER LOAD
demand_per_load = pd.read_csv(demand_per_load_path)
demand_per_load = {(int(row['Load']), int(row['Node'])): row['Demand'] for index, row in demand_per_load.iterrows()}

# BUSES
bus_reactance = pd.read_csv(bus_reactance_path)
bus_reactance = {(row['From Bus'], row['To Bus']): row['Reactance'] for index, row in bus_reactance.iterrows()}

bus_capacity = pd.read_csv(bus_capacity_path)
bus_capacity = {(row['From Bus'], row['To Bus']): row['Capacity'] for index, row in bus_capacity.iterrows()}

if __name__ == "__main__":
    # Use in case you want to access the data directly

    input_data = InputData(generators, bid_offers, system_demand, demand_per_load)

    # Accessing data for a specific unit
    print("Generators: ", input_data.generators)
    unit_id = 3
    print(f"Max Power for Unit {unit_id}: {input_data.Pmax[unit_id]} MW")
    print(f"Min Power for Unit {unit_id}: {input_data.Pmin[unit_id]} MW")
    print(f"Maximum up reserve capacity  for Unit {unit_id}: {input_data.Max_up_reserve[unit_id]} MW")
    print(f"Maximum down reserve capacity for Unit {unit_id}: {input_data.Max_down_reserve[unit_id]} MW")
    print(f"Up Time for Unit {unit_id}: {input_data.UT[unit_id]} hours")
    print(f"Down Time for Unit {unit_id}: {input_data.DT[unit_id]} hours")
    print(f"Ramp Up Rate for Unit {unit_id}: {input_data.RU[unit_id]} MW/h")
    print(f"Ramp Down Rate for Unit {unit_id}: {input_data.RD[unit_id]} MW/h")
