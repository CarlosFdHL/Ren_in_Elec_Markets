import numpy as np
# Description: This file contains the InputData class that is used to store the technical data for each generator and the system demand data.

# The class is used to instantiate an object that is passed to the model class to build the optimization model.
class InputData:
    def __init__(self, generators: list, bid_offers: dict, demand: list, demand_per_load: dict, bus_reactance: dict, bus_capacity: dict,zone_mapping: dict,):   
        # Initialize dictionaries to store the technical data for each generator
        self.generators = [i for i in range(1,len(generators)+1)]
        self.timeSpan = [i for i in range(1,2)]
        self.loads = [i for i in range(1,len(demand_per_load)+1)]
        self.nodes = [i for i in range(1,25)]
        self.zones = [i for i in range(1,3)] #2 zones
        self.Pmax = {}
        self.Pmin = {}
        self.Max_up_reserve = {}
        self.Max_down_reserve = {}
        self.UT = {}
        self.DT = {}
        self.RU = {}
        self.RD = {}
        self.wind = {}
        self.P_node = {}
        self.bid_offers = bid_offers
        self.demand = demand
        self.demand_bid_price = [] 
        self.demand_per_load = demand_per_load
        self.bus_reactance = bus_reactance  # Store bus_reactance
        self.bus_capacity = bus_capacity  # Store bus_capacity
        self.zone_mapping = zone_mapping  # Store zone_mapping
        self.atc = []


        #Adjust demand
        num_hours = len(self.timeSpan)
        num_days = num_hours // 24
        if num_hours <= 24:
            factor = 24 / num_hours
            adjusted_demand = [self.demand[int(i * factor)] for i in range(num_hours)]
        else:
            # Repeats the demands in order
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
        print("Demand bid price: ", self.demand_bid_price)

# Example data as you might get from a database or input file
wind_CF = [0.584,0.609,0.616,0.612,0.614,0.617,0.607,0.611,0.607,0.625,0.644,0.658,0.661,0.656,0.674,0.702,0.717,0.726,0.742,0.773,0.778,0.763,0.742,0.743] # Capacity factor pu (P.nominal = 200 MW)
wind_CF = [cf * 200 for cf in wind_CF]

generators = [
    {'Unit #': 1, 'Node': 1, 'Pmax (MW)': 152, 'Pmin (MW)': 30.4, 'R+ (MW)': 40, 'R- (MW)': 40, 'RU (MW/h)': 120, 'RD (MW/h)': 120, 'UT (h)': 8, 'DT (h)': 4, 'wind': False},
    {'Unit #': 2, 'Node': 2, 'Pmax (MW)': 152, 'Pmin (MW)': 30.4, 'R+ (MW)': 40, 'R- (MW)': 40, 'RU (MW/h)': 120, 'RD (MW/h)': 120, 'UT (h)': 8, 'DT (h)': 4, 'wind': False},
    {'Unit #': 3, 'Node': 7, 'Pmax (MW)': 350, 'Pmin (MW)': 75, 'R+ (MW)': 70, 'R- (MW)': 70, 'RU (MW/h)': 350, 'RD (MW/h)': 350, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    {'Unit #': 4, 'Node': 13, 'Pmax (MW)': 591, 'Pmin (MW)': 206.85, 'R+ (MW)': 180, 'R- (MW)': 180, 'RU (MW/h)': 240, 'RD (MW/h)': 240, 'UT (h)': 12, 'DT (h)': 10, 'wind': False},
    {'Unit #': 5, 'Node': 16, 'Pmax (MW)': 60, 'Pmin (MW)': 12, 'R+ (MW)': 60, 'R- (MW)': 60, 'RU (MW/h)': 60, 'RD (MW/h)': 60, 'UT (h)': 4, 'DT (h)': 2, 'wind': False},
    {'Unit #': 6, 'Node': 15, 'Pmax (MW)': 155, 'Pmin (MW)': 54.25, 'R+ (MW)': 30, 'R- (MW)': 30, 'RU (MW/h)': 155, 'RD (MW/h)': 155, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    {'Unit #': 7, 'Node': 16, 'Pmax (MW)': 155, 'Pmin (MW)': 54.25, 'R+ (MW)': 30, 'R- (MW)': 30, 'RU (MW/h)': 155, 'RD (MW/h)': 155, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    {'Unit #': 8, 'Node': 18, 'Pmax (MW)': 400, 'Pmin (MW)': 100, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 280, 'RD (MW/h)': 280, 'UT (h)': 1, 'DT (h)': 1, 'wind': False},
    {'Unit #': 9, 'Node': 21, 'Pmax (MW)': 400, 'Pmin (MW)': 100, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 280, 'RD (MW/h)': 280, 'UT (h)': 1, 'DT (h)': 1, 'wind': False},
    {'Unit #': 10, 'Node': 22, 'Pmax (MW)': 300, 'Pmin (MW)': 300, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 300, 'RD (MW/h)': 300, 'UT (h)': 0, 'DT (h)': 0, 'wind': False},
    {'Unit #': 11, 'Node': 23, 'Pmax (MW)': 310, 'Pmin (MW)': 108.5, 'R+ (MW)': 60, 'R- (MW)': 60, 'RU (MW/h)': 180, 'RD (MW/h)': 180, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    {'Unit #': 12, 'Node': 23, 'Pmax (MW)': 350, 'Pmin (MW)': 140, 'R+ (MW)': 40, 'R- (MW)': 40, 'RU (MW/h)': 240, 'RD (MW/h)': 240, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    #6 additional Wind farms
    {'Unit #': 13, 'Node': 3,'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 14, 'Node': 5,'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 15, 'Node': 7,'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 16, 'Node': 16,'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 17, 'Node': 21,'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 18, 'Node': 23,'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True}
]

for gen in generators:
    if not gen['wind']:
        gen['Pmin (MW)'] = 0

bid_offers = {
    1: 13.32, 2: 13.32, 3: 20.7, 4: 20.93, 5: 26.11, 6: 10.52, 7: 10.52, 8: 6.02, 9: 5.47, 10: 0, 11: 10.52, 12: 10.89, 
    13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0 # Wind farms
}

# System demand values in MW for each hour
system_demand = [
    1775.835, 1669.815, 1590.3, 1563.795, 1563.795, 
    1590.3, 1961.37, 2279.43, 2517.975, 2544.48, 
    2544.48, 2517.975, 2517.975, 2517.975, 2464.965, 
    2464.965, 2623.995, 2650.5, 2650.5, 2544.48, 
    2411.955, 2199.915, 1934.865, 1669.815
]

demand_per_load = {
    (1, 1): 3.8, (2, 2): 3.4, (3, 3): 6.3, (4, 4):2.6, 
    (5, 5):2.5, (6, 6):4.8, (7, 7):4.4, (8, 8):6, 
    (9, 9):6.1, (10, 10):6.8, (11, 13):9.3, (12, 14):6.8, 
    (13, 15):11.1, (14, 16):3.5, (15, 18):11.7, (16, 19):6.4, 
    (17, 20):4.5, (18, 11): 0, (19, 12): 0, (20, 17): 0, 
    (21, 21): 0, (22, 22): 0, (23, 23): 0, (24, 24): 0
}

#Tranmission lines Table 5 
# Dictionary for Reactance (p.u.)
bus_reactance = {
    (1, 2): 0.0146, (1, 3): 0.2253, (1, 5): 0.0907, (2, 4): 0.1356, (2, 6): 0.205,
    (3, 9): 0.1271, (3, 24): 0.084, (4, 9): 0.111, (5, 10): 0.094, (6, 10): 0.0642,
    (7, 8): 0.0652, (8, 9): 0.1762, (8, 10): 0.1762, (9, 11): 0.084, (9, 12): 0.084,
    (10, 12): 0.084, (11, 13): 0.0488, (11, 14): 0.0426, (12, 13): 0.0488, (12, 23): 0.0985,
    (13, 23): 0.0884, (14, 16): 0.0594, (15, 16): 0.0172, (15, 21): 0.249, (15, 24): 0.0529,
    (16, 17): 0.0234, (17, 18): 0.0143, (17, 22): 0.1069, (18, 21): 0.0132, (19, 20): 0.0203,
    (20, 23): 0.034, (21, 22): 0.0692
}

# Dictionary for Capacity (MVA)
bus_capacity = {
    (1, 2): 175, (1, 3): 175, (1, 5): 350, (2, 4): 175, (2, 6): 175,
    (3, 9): 175, (3, 24): 400, (4, 9): 175, (5, 10): 350, (6, 10): 175,
    (7, 8): 350, (8, 9): 175, (8, 10): 175, (9, 11): 400, (9, 12): 400,
    (10, 12): 400, (11, 13): 500, (11, 14): 500, (12, 13): 500, (12, 23): 500,
    (13, 23): 500, (14, 16): 500, (15, 16): 500, (15, 21): 1000, (15, 24): 500,
    (16, 17): 500, (17, 18): 500, (17, 22): 500, (18, 21): 1000, (19, 20): 1000,
    (20, 23): 1000, (21, 22): 500
}

# Zonal Framework 
# Assign zones to nodes
# Zone A: 1-12, Zone B: 13-24
zone_mapping = {
    1: "Zone A", 2: "Zone A", 3: "Zone A", 4: "Zone A",
    5: "Zone A", 6: "Zone A", 7: "Zone A", 8: "Zone A",
    9: "Zone A", 10: "Zone A", 11: "Zone A", 12: "Zone A",
    13: "Zone B", 14: "Zone B", 15: "Zone B", 16: "Zone B",
    17: "Zone B", 18: "Zone B", 19: "Zone B", 20: "Zone B", 
    21: "Zone B", 22: "Zone B", 23: "Zone B", 24: "Zone B"
}




if __name__ == "__main__":
    # Use in case you want to access the data directly

    input_data = InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity,zone_mapping, atc = {})

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
    print("\nZonal Framework:")
    for node, zone in zone_mapping.items():
        print(f"Node {node} → {zone}")
