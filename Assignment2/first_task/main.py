import matplotlib.pyplot as plt
import sys

from .input_data import *
from .model_one_price import OnePriceBiddingModel
from .model_two_price import TwoPriceBiddingModel
from .expost_analysis import ExPostAnalysis
from .plotting import plot_comparison_bids


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("Usage: python main.py [one_price|two_price]")

    model_type = sys.argv[1].lower()

    if model_type == 'one_price':
        model_class = OnePriceBiddingModel
    elif model_type == 'two_price':
        model_class = TwoPriceBiddingModel
    else:
        raise ValueError("Invalid model type. Use 'one_price' or 'two_price'.")

    # input_data = InputData(T, W, scenarios, prob_scenario)
    # model = model_class(input_data)
    # model.run()
    # model.print_results()
    # model.plot()
    
    #plot_comparison_bids(model_one_price, model_two_price)
    # Create an instance of ImputData
    # input_data = InputData(T, W, scenarios, prob_scenario)
    # model_one_price = OnePriceBiddingModel(input_data)
    # model_one_price.run()
    # model_one_price.print_results()
    # model_one_price.plot()

    # model_two_price = TwoPriceBiddingModel(input_data)
    # model_two_price.run() 
    # model_two_price.print_results()
    # model_two_price.plot()


    # Ex-post analysis
    model_expost = ExPostAnalysis(num_folds=8, scenarios=cv_scenarios, indices=cv_combinations, timeSpan=T, model_type=model_type, verbose=True)
    cv_results = model_expost.cross_validation(insample_size=200, outsample_size=1400)
    plt.show()

    print("\nEnd of main.py\n")

