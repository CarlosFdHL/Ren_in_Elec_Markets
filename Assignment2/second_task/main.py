import time

from .input_data import *
from .model_ancilliary import AncilliaryServiceBiddingModel


if __name__ == "__main__":
    start_time = time.time() # Start timer

    input_data = InputData(insample_scenarios, out_of_sample_scenarios, epsilon_requirement=0.1, num_hours=24)
    model = AncilliaryServiceBiddingModel(input_data, verbose=True)
    model.run_relaxed()
    model.print_results()
    
    end_time = time.time()  # End timer
    elapsed_time = end_time - start_time  # Calculate elapsed time

    print(f"Total execution time: {elapsed_time:.2f} seconds")
    print("End of main.py")