import sys
import matplotlib.pyplot as plt
import pandas as pd

from input_data import *
from model_one_price import OnePriceBiddingModel
from model_two_price import TwoPriceBiddingModel
from expost_analysis import ExPostAnalysis

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
    insample_sizes = range(100, 400, 20)  
    sensitivity_results = []

    for insample_size in insample_sizes:
        outsample_size = 1600 - insample_size
        print(f"\n>>> insample={insample_size}, outsample={outsample_size}")

        # Do Cross-validation
        cv_results = model_expost.cross_validation(insample_size=insample_size, outsample_size=outsample_size)

        # Calculate average profit difference
        avg_difference = np.mean([r["difference"] for r in cv_results])
        avg_relative_diff = np.mean([r["relative_difference"] for r in cv_results])


        print(f"Average profit difference: {round(avg_difference, 1)}")
        print(f"Average relative difference: {round(avg_relative_diff, 1)}")
        # Save results
        sensitivity_results.append({
            "insample_size": insample_size,
            "outsample_size": outsample_size,
            "avg_profit_difference": np.abs(avg_difference),
            "avg_relative_difference": np.abs(avg_relative_diff)
        })
    df_sensitivity = pd.DataFrame(sensitivity_results)

    # Plot
    plt.figure(figsize=(8, 5))
    plt.plot(df_sensitivity["insample_size"], df_sensitivity["avg_profit_difference"], marker="o")
    plt.xlabel("In-sample size")
    plt.ylabel("Average profit difference")
    plt.title("Sensitivity analysis: in-sample size vs profit difference")
    plt.grid(True)
    plt.tight_layout()

    plt.figure(figsize=(8, 5))
    plt.plot(df_sensitivity["insample_size"], df_sensitivity["avg_relative_difference"], marker="o", color="orange")
    plt.xlabel("In-sample size")
    plt.ylabel("Average relative profit difference (%)")
    plt.title("Sensitivity analysis: in-sample size vs relative profit difference")
    plt.grid(True)
    plt.tight_layout()

    plt.show()
