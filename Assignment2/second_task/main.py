import time

from .input_data import *
from .model_ancilliary import AncilliaryServiceBiddingModel
from .model_ancilliary_cvar import AncilliaryServiceBiddingModelCVAR
# from .model_ancilliary_pyomo import AncilliaryServiceBiddingModelPyomo

if __name__ == "__main__":
    start_time = time.time() # Start timer

    input_data = InputData(
        insample_scenarios, 
        out_of_sample_scenarios, 
        prob_scenarios_insample=prob_scenarios_insample,
        prob_scenarios_outsample=prob_scenarios_outsample, 
        epsilon_requirement=0.1, 
        num_hours=1,
    )
    model = AncilliaryServiceBiddingModel(input_data, verbose=True)
    model.run_hourly()
    # model.run_relaxed()
    # model.run()
    model.print_results()
    model.verify_p90_out_of_sample()

    model_cvar = AncilliaryServiceBiddingModelCVAR(input_data, verbose=True)
    model_cvar.run()
    model_cvar.print_results()
    model_cvar.verify_p90_out_of_sample()

    # model = AncilliaryServiceBiddingModelPyomo(input_data, verbose = True, solver = 'highs')
    # bids, violations, violation_count = model.run()
    # print("Bids:", bids)
    end_time = time.time()  # End timer
    elapsed_time = end_time - start_time  # Calculate elapsed time

    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")
    print("End of main.py")