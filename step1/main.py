from input_data import *
from model import Step1_model
from plotting import plotting_results




if __name__ == "__main__":
    # Solves the model with the data provided in the input_data.py file

    input_data = InputData(generators, bid_offers, system_demand, demand_per_load)
    model = Step1_model(input_data)
    model.run()
    model.print_results()

    plotting_results(model)
    
    print("End of main.py")