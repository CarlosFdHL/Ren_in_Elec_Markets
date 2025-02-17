import numpy as np
# Description: This file contains the InputData class that is used to store the technical data for each generator and the system demand data.

# The class is used to instantiate an object that is passed to the model class to build the optimization model.
class InputData:
    def __init__(self, generators: list, bid_offers: dict, demand: list, demand_per_load: dict):  
        # Initialize dictionaries to store the technical data for each generator
        self.generators = [i for i in range(1,len(generators)+1)]
        self.timeSpan = [i for i in range(1,25)]
        self.loads = [i for i in range(1,len(demand_per_load)+1)]
        self.Pmax = {}
        self.Pmin = {}
        self.Max_up_reserve = {}
        self.Max_down_reserve = {}
        self.UT = {}
        self.DT = {}
        self.RU = {}
        self.RD = {}
        self.wind = {}
        self.bid_offers = bid_offers
        self.demand = demand
        self.demand_bid_price = [] 
        self.demand_per_load = demand_per_load
        self.max_battery_storage = 3000 # MWh
        self.max_battery_charging_power = 300 # MW
        self.max_battery_discharging_power = 300 # MW
        self.battery_change_efficiency = 0.8
        self.battery_discharge_efficiency = 0.9

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

# Example data as you might get from a database or input file
wind_CF = [0.584,0.609,0.616,0.612,0.614,0.617,0.607,0.611,0.607,0.625,0.644,0.658,0.661,0.656,0.674,0.702,0.717,0.726,0.742,0.773,0.778,0.763,0.742,0.743] # Capacity factor pu (P.nominal = 200 MW)
wind_CF = [cf * 200 for cf in wind_CF]
generators = [
    {'Unit #': 1, 'Pmax (MW)': 152, 'Pmin (MW)': 30.4, 'R+ (MW)': 40, 'R- (MW)': 40, 'RU (MW/h)': 120, 'RD (MW/h)': 120, 'UT (h)': 8, 'DT (h)': 4, 'wind': False},
    {'Unit #': 2, 'Pmax (MW)': 152, 'Pmin (MW)': 30.4, 'R+ (MW)': 40, 'R- (MW)': 40, 'RU (MW/h)': 120, 'RD (MW/h)': 120, 'UT (h)': 8, 'DT (h)': 4, 'wind': False},
    {'Unit #': 3, 'Pmax (MW)': 350, 'Pmin (MW)': 75, 'R+ (MW)': 70, 'R- (MW)': 70, 'RU (MW/h)': 350, 'RD (MW/h)': 350, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    {'Unit #': 4, 'Pmax (MW)': 591, 'Pmin (MW)': 206.85, 'R+ (MW)': 180, 'R- (MW)': 180, 'RU (MW/h)': 240, 'RD (MW/h)': 240, 'UT (h)': 12, 'DT (h)': 10, 'wind': False},
    {'Unit #': 5, 'Pmax (MW)': 60, 'Pmin (MW)': 12, 'R+ (MW)': 60, 'R- (MW)': 60, 'RU (MW/h)': 60, 'RD (MW/h)': 60, 'UT (h)': 4, 'DT (h)': 2, 'wind': False},
    {'Unit #': 6, 'Pmax (MW)': 155, 'Pmin (MW)': 54.25, 'R+ (MW)': 30, 'R- (MW)': 30, 'RU (MW/h)': 155, 'RD (MW/h)': 155, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    {'Unit #': 7, 'Pmax (MW)': 155, 'Pmin (MW)': 54.25, 'R+ (MW)': 30, 'R- (MW)': 30, 'RU (MW/h)': 155, 'RD (MW/h)': 155, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    {'Unit #': 8, 'Pmax (MW)': 400, 'Pmin (MW)': 100, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 280, 'RD (MW/h)': 280, 'UT (h)': 1, 'DT (h)': 1, 'wind': False},
    {'Unit #': 9, 'Pmax (MW)': 400, 'Pmin (MW)': 100, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 280, 'RD (MW/h)': 280, 'UT (h)': 1, 'DT (h)': 1, 'wind': False},
    {'Unit #': 10, 'Pmax (MW)': 300, 'Pmin (MW)': 300, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 300, 'RD (MW/h)': 300, 'UT (h)': 0, 'DT (h)': 0, 'wind': False},
    {'Unit #': 11, 'Pmax (MW)': 310, 'Pmin (MW)': 108.5, 'R+ (MW)': 60, 'R- (MW)': 60, 'RU (MW/h)': 180, 'RD (MW/h)': 180, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    {'Unit #': 12, 'Pmax (MW)': 350, 'Pmin (MW)': 140, 'R+ (MW)': 40, 'R- (MW)': 40, 'RU (MW/h)': 240, 'RD (MW/h)': 240, 'UT (h)': 8, 'DT (h)': 8, 'wind': False},
    #6 additional Wind farms
    {'Unit #': 13, 'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 14, 'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 15, 'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 16, 'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 17, 'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True},
    {'Unit #': 18, 'Pmax (MW)': wind_CF, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0, 'wind': True}
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
    1: 3.8, 2: 3.4, 3: 6.3, 4:2.6, 5:2.5, 6:4.8, 7:4.4, 8:6, 9:6.1, 10:6.8, 11:9.3, 12:6.8, 13:11.1, 14:3.5, 15:11.7, 16:6.4, 17:4.5
}

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
