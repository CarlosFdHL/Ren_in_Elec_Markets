from input_data import *
from model import Step2_model
from plotting import plotting_results #plot_generation_and_bid




if __name__ == "__main__":
    # Solves the model with the data provided in the input_data.py file

    input_data = InputData(generators, bid_offers, system_demand, demand_per_load, p_initial)
    model = Step2_model(input_data)
    model.run()
    model.print_results()

    plotting_results(model)
    '''plot_generation_and_bid(input_data)'''

    print("End of main.py")