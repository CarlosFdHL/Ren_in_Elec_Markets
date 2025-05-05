import numpy as np
import pandas as pd
import os
import glob
import itertools
import random
random.seed(5) # Use a fixed seed for reproducibility

class InputData:
    def __init__(self, insample_scenarios, out_of_sample_scenarios, epsilon_requirement = 0.1, num_hours = 24):
        """
        Initializes the InputData class by loading and processing scenario data.

        Args:
            num_samples (int): Number of scenarios for main model training/evaluation.
                               Needs to be >= 2 for P90 model split.
            cv_nsamples (int): Number of scenarios for cross-validation (if used elsewhere).
        """
        self.M = [i for i in range(0,60)] # Minutes in 1 hour
        self.W = [i for i in range(0,100)] # Number of insample scenarios
        self.H = [i for i in range(0,num_hours)] # Number of hours

        self.num_hours = num_hours
        
        self.insample_scenarios = insample_scenarios
        self.out_of_sample_scenarios = out_of_sample_scenarios

        self.max_violated_scenarios = epsilon_requirement * len(self.W) * len(self.M) # Maximum number of violations

# PATHS
script_dir = os.path.dirname(__file__)

insample_dir = os.path.join(script_dir, '../data/consumption_profiles/in_sample_profiles.csv')
in_sample_profiles = pd.read_csv(insample_dir, sep=',')
insample_scenarios = {
    (m, w): in_sample_profiles.iloc[w, m]
    for w in range(in_sample_profiles.shape[0])  # Number of rows (scenarios)
    for m in range(in_sample_profiles.shape[1])  # Number of columns (minutes)
}
out_of_sample_dir = os.path.join(script_dir, '../data/consumption_profiles/out_sample_profiles.csv')
out_of_sample_profiles = pd.read_csv(out_of_sample_dir, sep=',')
out_of_sample_scenarios = {
    (m, w + 1): out_of_sample_profiles.iloc[w, m]
    for w in range(out_of_sample_profiles.shape[0])  # Number of rows (scenarios)
    for m in range(out_of_sample_profiles.shape[1])  # Number of columns (minutes)
}
