from input_data import *
from model import Step1_model




if __name__ == "__main__":
    
    input_data = InputData(generators, bid_offers, system_demand, demand_bid_price)
    model = Step1_model(input_data)
    model.run()
    model.print_results()