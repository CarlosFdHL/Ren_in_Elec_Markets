from input_data_day_ahead import *
from day_ahead_model import DayAheadModel
from regulation_model import RegulationModel
from input_data_regulation import InputDataRegulation
from plotting import plotting_results
from plotting import plot_generation_and_bid as plotting_bid




if __name__ == "__main__":
    # Solves the model with the data provided in the input_data.py file

    input_data = InputDataDayAhead(generators, bid_offers, system_demand, demand_per_load)
    model_day_ahead = DayAheadModel(input_data)
    model_day_ahead.run()
    model_day_ahead.print_results()
    input_data_regulation = InputDataRegulation(model_day_ahead)
    regulation_model = RegulationModel(model_day_ahead, input_data_regulation)
    regulation_model.run()
    regulation_model.print_results()

    #plotting_results(model_day_ahead)
    
    #plotting_bid(input_data)

    print("End of main.py")