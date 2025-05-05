from .input_data import *
from .model_ancilliary import AncilliaryServiceBiddingModel


if __name__ == "__main__":
    input_data = InputData(insample_scenarios, out_of_sample_scenarios, epsilon_requirement=0.1, num_hours=24)
    model = AncilliaryServiceBiddingModel(input_data, verbose=True)
    model.run()
    model.print_results()
    
    print("End of main.py")