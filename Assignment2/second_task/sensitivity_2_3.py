import time
import numpy as np
import matplotlib.pyplot as plt

from .input_data import *
from .model_ancilliary import AncilliaryServiceBiddingModel

if __name__ == "__main__":
    start_time = time.time() # Start timer

    epsilons = np.arange(0, 0.25, 0.05)

    optimal_bids = []
    outsample_violations = []
    shortfall_violations = np.zeros(len(epsilons))

    for i, eps in enumerate(epsilons):
        print(f"\nRunning model with epsilon requirement: {eps:.2f}")
        input_data = InputData(
            insample_scenarios, 
            out_of_sample_scenarios, 
            prob_scenarios_insample=prob_scenarios_insample,
            prob_scenarios_outsample=prob_scenarios_outsample, 
            epsilon_requirement=eps, 
            num_hours=1,
        )
        model = AncilliaryServiceBiddingModel(input_data, verbose=False)
        model.run_hourly()
        model.print_results()

        # Store optimal bid (sum over hours if more than one)
        bid = model.results.bid_capacity[0]
        optimal_bids.append(bid)

        # Out-of-sample violations
        # Count total number of minutes where bid < out-of-sample scenario
        num_violations = 0
        num_minutes = len(input_data.M)
        num_profiles = input_data.n_outsample_scenarios
        for h in input_data.H:
            bid = model.results.bid_capacity[h]
            for w in range(num_profiles):
                for m in input_data.M:
                    idx = h * num_minutes + m
                    if bid > out_of_sample_scenarios[idx, w]:
                        num_violations += 1
                        shortfall_violations[i] += bid - out_of_sample_scenarios[idx, w] 
            shortfall_violations[i] /= num_profiles 
        outsample_violations.append(num_violations)
    relative_shortfall_violations = [shortfall / (optimal_bids[i]*60)*100 for i, shortfall in enumerate(shortfall_violations)]
    # Plot results
    xlabels = ['P100', 'P95', 'P90', 'P85', 'P80']

    fig, axs = plt.subplots(1, 2, figsize=(12, 5))
    axs[0].plot(xlabels, optimal_bids, marker='o')
    axs[0].set_xlabel('Epsilon requirement')
    axs[0].set_ylabel('Optimal Reserve Bid [kW]')
    # axs[0].set_title('Optimal Bid vs Epsilon')
    axs[0].grid()

    axs[1].plot(xlabels, relative_shortfall_violations, marker='o', color='red')
    axs[1].set_xlabel('Epsilon requirement')
    axs[1].set_ylabel('Out-of-sample Expected Shortfall [%]')
    # axs[1].set_title('Violations vs Epsilon')
    axs[1].grid()

    plt.tight_layout()
    plt.show()

    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")
    print("End of main.py")