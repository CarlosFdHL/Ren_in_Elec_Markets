import matplotlib.pyplot as plt

from .input_data import *
from .model_one_price import OnePriceBiddingModel
from .model_two_price import TwoPriceBiddingModel
from .plotting import plot_comparison_bids

if __name__ == "__main__":
    # Create an instance of ImputData
    input_data = InputData(T, W, scenarios, prob_scenario)
    model_one_price = OnePriceBiddingModel(input_data)
    model_one_price.run()
    model_one_price.print_results()
    model_one_price.plot()

    model_two_price = TwoPriceBiddingModel(input_data)
    model_two_price.run() 
    model_two_price.print_results()
    model_two_price.plot()

    plot_comparison_bids(model_one_price, model_two_price)

    plt.show()

