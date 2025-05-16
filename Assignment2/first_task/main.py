import matplotlib.pyplot as plt
import sys
import time

from .input_data import *
from .model_one_price import OnePriceBiddingModel
from .model_two_price import TwoPriceBiddingModel
from .expost_analysis import ExPostAnalysis
from .plotting import plot_comparison_bids



if __name__ == "__main__":
    start_time = time.time() # Start timer
    if len(sys.argv) != 2:
        raise ValueError("Usage: python main.py [one_price|two_price]")

    model_type = sys.argv[1].lower()

    if model_type == 'one_price':
        model_class = OnePriceBiddingModel
    elif model_type == 'two_price':
        model_class = TwoPriceBiddingModel
    else:
        raise ValueError("Invalid model type. Use 'one_price' or 'two_price'.")

    # --------------------------------------------------------------------------------
    #                    1st and 2nd Task - One and Two Price Bidding
    # --------------------------------------------------------------------------------
    # Run only one of the models at a time:

    input_data = InputData(T, W, scenarios, prob_scenario, model_type=model_type)
    model = model_class(input_data)
    model.run()
    model.print_results()
    model.plot()

    #
    # Run both models and compare the results:
    #
    
    # input_data = InputData(T, W, scenarios, prob_scenario, model_type = 'one_price')
    # model_one_price = OnePriceBiddingModel(input_data)
    # model_one_price.run()
    #
    # input_data = InputData(T, W, scenarios, prob_scenario, model_type = 'two_price')
    # model_two_price = TwoPriceBiddingModel(input_data)
    # model_two_price.run() 
    #
    # plot_comparison_bids(model_one_price, model_two_price)

    # --------------------------------------------------------------------------------
    #                           3rd Task - Expost Analysis 
    # --------------------------------------------------------------------------------
    #
    # Run only expost analysis on the specified model type:

    #model_expost = ExPostAnalysis(timeSpan=T, scenarios=cv_scenarios, model_type=model_type, verbose=True)
    #cv_results = model_expost.cross_validation(K = 8)

    # In order to run the CV analysis run: python -m first_task.sensitivity_expost one_price/two_price

    # Show generated plots
    plt.show()
    end_time = time.time()  # End timer
    elapsed_time = end_time - start_time  # Calculate elapsed time

    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")
    print("\nEnd of main.py\n")

