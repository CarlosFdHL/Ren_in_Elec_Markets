from .input_data import *
from .model import TwoPriceBiddingModel

if __name__ == "__main__":
    # Create an instance of ImputData
    input_data = InputData(T, W, scenarios, prob_scenario)
    model = TwoPriceBiddingModel(input_data)
    model.run()
    model.print_results()
