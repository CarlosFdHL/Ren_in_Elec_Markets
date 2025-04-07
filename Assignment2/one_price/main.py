from .input_data import *
from .model import OnePriceBiddingModel

if __name__ == "__main__":
    # Create an instance of ImputData
    input_data = InputData(T, W, scenarios, prob_scenario)
    model = OnePriceBiddingModel(input_data)
    model.run()
    model.print_results()
