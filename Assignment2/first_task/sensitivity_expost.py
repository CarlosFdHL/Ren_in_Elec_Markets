import sys
import matplotlib.pyplot as plt
import pandas as pd
import time

from .input_data import *
from .model_one_price import OnePriceBiddingModel
from .model_two_price import TwoPriceBiddingModel
from .expost_analysis import ExPostAnalysis

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
    

    # Trying to run the cross-validation with different in-sample sizes
    K = [3, 4, 5, 6, 7, 8, 9, 10]
    insample_sizes = [len(cv_scenarios)//k for k in K] 

    # Store results in array of dictionaries
    sensitivity_results = []
    for i, k in enumerate(K):
        print(f"\n>>> KFold: {k}")
        
        # Define the model
        model_expost = ExPostAnalysis(timeSpan=T, scenarios=cv_scenarios, model_type=model_type, verbose=False)
        
        cv_results = model_expost.cross_validation(k)

        # Calculate average profit difference
        avg_insample_profit = np.mean([r["insample_expected_profit"] for r in cv_results])
        avg_outofsample_profit = np.mean([r["outofsample_expected_profit"] for r in cv_results])
        diff_of_averages = avg_insample_profit - avg_outofsample_profit
        relative_diff_of_averages = (diff_of_averages / avg_insample_profit) * 100
        
        # Log results
        print(f"Difference of the average profits: {round(diff_of_averages, 3)}")
        print(f"Relative difference of the average profits: {round(relative_diff_of_averages, 3)}")

        # Save results
        sensitivity_results.append({
            "insample_size": insample_sizes[i],
            "outsample_size": len(cv_scenarios) - insample_sizes[i],
            "diff_of_averages": np.abs(diff_of_averages),
            "relative_diff_of_averages": np.abs(relative_diff_of_averages)
        })
    df_sensitivity = pd.DataFrame(sensitivity_results)

    # Plot
    # plt.figure(figsize=(9, 6))
    # plt.plot(df_sensitivity["insample_size"], df_sensitivity["diff_of_averages"], marker="o")
    # plt.xlabel("In-sample size")
    # plt.ylabel("Difference of avg. expected profit (in vs. out)")
    # # plt.title("Sensitivity analysis: in-sample size vs profit difference")
    # plt.grid(True)
    # plt.tight_layout()

    plt.figure(figsize=(9, 6))
    plt.plot(df_sensitivity["insample_size"], df_sensitivity["relative_diff_of_averages"], marker="o", color="orange")
    plt.xlabel("In-sample size")
    plt.ylabel("Relative difference of in-/out-sample avg. expected profit (%)")
    # plt.title("Sensitivity analysis: in-sample size vs relative profit difference")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    end_time = time.time()  # End timer
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")