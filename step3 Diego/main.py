from input_data import *
from model import Step3_zonal




if __name__ == "__main__":
    # Solves the model with the data provided in the input_data.py file

    input_data = InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity,zone_mapping)
    model = Step3_zonal(input_data)
    model.run()
    model.print_results()

    print("End of main.py")