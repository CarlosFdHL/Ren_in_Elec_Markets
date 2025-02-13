class InputData:
    def __init__(self, generators: list, bid_offers: list, demand: list, demand_bid_price: float):  
        # Initialize dictionaries to store the technical data for each generator
        self.generators = [i for i in range(1,13)]
        self.timeSpan = [i for i in range(1,2)]
        self.Pmax = {}
        self.Pmin = {}
        self.Max_up_reserve = {}
        self.Max_down_reserve = {}
        self.UT = {}
        self.DT = {}
        self.RU = {}
        self.RD = {}
        self.bid_offers = bid_offers
        self.demand = demand
        self.demand_bid_price = demand_bid_price

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

# Example data as you might get from a database or input file
generators = [
    {'Unit #': 1, 'Pmax (MW)': 152, 'Pmin (MW)': 30.4, 'R+ (MW)': 40, 'R- (MW)': 40, 'RU (MW/h)': 120, 'RD (MW/h)': 120, 'UT (h)': 8, 'DT (h)': 4},
    {'Unit #': 2, 'Pmax (MW)': 152, 'Pmin (MW)': 30.4, 'R+ (MW)': 40, 'R- (MW)': 40, 'RU (MW/h)': 120, 'RD (MW/h)': 120, 'UT (h)': 8, 'DT (h)': 4},
    {'Unit #': 3, 'Pmax (MW)': 350, 'Pmin (MW)': 75, 'R+ (MW)': 70, 'R- (MW)': 70, 'RU (MW/h)': 350, 'RD (MW/h)': 350, 'UT (h)': 8, 'DT (h)': 8},
    {'Unit #': 4, 'Pmax (MW)': 591, 'Pmin (MW)': 206.85, 'R+ (MW)': 180, 'R- (MW)': 180, 'RU (MW/h)': 240, 'RD (MW/h)': 240, 'UT (h)': 12, 'DT (h)': 10},
    {'Unit #': 5, 'Pmax (MW)': 60, 'Pmin (MW)': 12, 'R+ (MW)': 60, 'R- (MW)': 60, 'RU (MW/h)': 60, 'RD (MW/h)': 60, 'UT (h)': 4, 'DT (h)': 2},
    {'Unit #': 6, 'Pmax (MW)': 155, 'Pmin (MW)': 54.25, 'R+ (MW)': 30, 'R- (MW)': 30, 'RU (MW/h)': 155, 'RD (MW/h)': 155, 'UT (h)': 8, 'DT (h)': 8},
    {'Unit #': 7, 'Pmax (MW)': 155, 'Pmin (MW)': 54.25, 'R+ (MW)': 30, 'R- (MW)': 30, 'RU (MW/h)': 155, 'RD (MW/h)': 155, 'UT (h)': 8, 'DT (h)': 8},
    {'Unit #': 8, 'Pmax (MW)': 400, 'Pmin (MW)': 100, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 280, 'RD (MW/h)': 280, 'UT (h)': 1, 'DT (h)': 1},
    {'Unit #': 9, 'Pmax (MW)': 400, 'Pmin (MW)': 100, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 280, 'RD (MW/h)': 280, 'UT (h)': 1, 'DT (h)': 1},
    {'Unit #': 10, 'Pmax (MW)': 300, 'Pmin (MW)': 300, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 300, 'RD (MW/h)': 300, 'UT (h)': 0, 'DT (h)': 0},
    {'Unit #': 11, 'Pmax (MW)': 310, 'Pmin (MW)': 108.5, 'R+ (MW)': 60, 'R- (MW)': 60, 'RU (MW/h)': 180, 'RD (MW/h)': 180, 'UT (h)': 8, 'DT (h)': 8},
    {'Unit #': 12, 'Pmax (MW)': 350, 'Pmin (MW)': 140, 'R+ (MW)': 40, 'R- (MW)': 40, 'RU (MW/h)': 240, 'RD (MW/h)': 240, 'UT (h)': 8, 'DT (h)': 8},
    #6 additional Wind turbines
    {'Unit #': 13, 'Pmax (MW)': 200, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0},
    {'Unit #': 14, 'Pmax (MW)': 200, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0},
    {'Unit #': 15, 'Pmax (MW)': 200, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0},
    {'Unit #': 16, 'Pmax (MW)': 200, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0},
    {'Unit #': 17, 'Pmax (MW)': 200, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0},
    {'Unit #': 18, 'Pmax (MW)': 200, 'Pmin (MW)': 0, 'R+ (MW)': 0, 'R- (MW)': 0, 'RU (MW/h)': 100, 'RD (MW/h)': 100, 'UT (h)': 0, 'DT (h)': 0}
]

#!!!! CHANGE VALUES
bid_offers = [13.32, 20.7, 20.93, 26.11, 10.52, 10.52, 6.02, 5.47, 0, 10.52, 10.89, 10.89]  # Adjusted to match the number of units

# System demand values in MW for each hour
system_demand = [
    1775.835, 1669.815, 1590.3, 1563.795, 1563.795, 
    1590.3, 1961.37, 2279.43, 2517.975, 2544.48, 
    2544.48, 2517.975, 2517.975, 2517.975, 2464.965, 
    2464.965, 2623.995, 2650.5, 2650.5, 2544.48, 
    2411.955, 2199.915, 1934.865, 1669.815
]
demand_bid_price = 15 # $/MWh

# Try class InputData
"""
input_data = InputData(generators)

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
"""
