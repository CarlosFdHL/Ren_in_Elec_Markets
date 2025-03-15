from input_data import *
from day_ahead_model import Step6_model
from reserve_model import *
from plotting import plotting_results
from plotting import plot_generation_and_bid as plotting_bid




if __name__ == "__main__":
    # Solves the model with the data provided in the input_data.py file

    input_data = InputData(generators, bid_offers, system_demand, demand_per_load, bid_reserve_up, bid_reserve_down)

    reserve_model = ReserveModel(input_data)
    reserve_model.run()
    reserve_model.print_results()

    model = Step6_model(input_data, reserve_model.results)
    model.run()
    model.print_results()

    plotting_results(model)
    
    plotting_bid(input_data)

    print("End of main.py")