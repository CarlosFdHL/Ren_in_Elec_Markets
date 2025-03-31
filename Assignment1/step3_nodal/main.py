from input_data import *
from model import Step3_model



def run_model(input_data):
    # Solves the model with the data provided in the input_data.py file
    model = Step3_model(input_data)
    model.run()
    model.print_results() 

    return model.results.nodal_price


if __name__ == "__main__":
    # Default input data
    input_data = InputData(generators, bid_offers, system_demand, demand_per_load, bus_reactance, bus_capacity)
    run_model(input_data)
    
    print("End of main.py")
