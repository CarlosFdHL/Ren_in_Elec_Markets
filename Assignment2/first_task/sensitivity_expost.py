import sys
import matplotlib.pyplot as plt
import pandas as pd

from .input_data import *
from .model_one_price import OnePriceBiddingModel
from .model_two_price import TwoPriceBiddingModel
from .expost_analysis import ExPostAnalysis

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
    

    # Define the model
    model_expost = ExPostAnalysis(num_folds=8, scenarios=cv_scenarios, indices=cv_combinations, timeSpan=T, model_type=model_type, verbose=False)

    # Trying to run the cross-validation with different in-sample sizes
    K = [3, 4, 5, 6, 7, 8, 9, 10]
    insample_sizes = [1600//k for k in K] 
    sensitivity_results = []

    for i, k in enumerate(K):
        # outsample_size = 1600 - insample_size
        # print(f"\n>>> insample={insample_size}, outsample={outsample_size}")
        # Do Cross-validation
        cv_results = model_expost.cross_validation(k)

        # Calculate average profit difference
        avg_insample_profit = np.mean([r["insample_expected_profit"] for r in cv_results])
        avg_outofsample_profit = np.mean([r["outofsample_expected_profit"] for r in cv_results])
        diff_of_averages = avg_insample_profit - avg_outofsample_profit
        relative_diff_of_averages = (diff_of_averages / avg_insample_profit) * 100
        

        print(f"Difference of the average profits: {round(diff_of_averages, 1)}")
        print(f"Relative difference of the average profits: {round(relative_diff_of_averages, 1)}")
        # Save results
        sensitivity_results.append({
            "insample_size": insample_sizes[i],
            "outsample_size": 1600 - insample_sizes[i],
            "diff_of_averages": np.abs(diff_of_averages),
            "relative_diff_of_averages": np.abs(relative_diff_of_averages)
        })
    df_sensitivity = pd.DataFrame(sensitivity_results)

    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(df_sensitivity["insample_size"], df_sensitivity["diff_of_averages"], marker="o")
    plt.xlabel("In-sample size")
    plt.ylabel("Difference of average expected profit of in and out sample")
    # plt.title("Sensitivity analysis: in-sample size vs profit difference")
    plt.grid(True)
    plt.tight_layout()

    plt.figure(figsize=(8, 5))
    plt.plot(df_sensitivity["insample_size"], df_sensitivity["relative_diff_of_averages"], marker="o", color="orange")
    plt.xlabel("In-sample size")
    plt.ylabel("Relative difference of average expected profit of in and out sample (%)")
    # plt.title("Sensitivity analysis: in-sample size vs relative profit difference")
    plt.grid(True)
    plt.tight_layout()

    plt.show()
