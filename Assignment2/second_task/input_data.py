import numpy as np
import pandas as pd
import os
import glob
import itertools
import random
random.seed(5) # Use a fixed seed for reproducibility

class InputData:
    def __init__(self, num_samples=200, cv_nsamples=1600): # Allow configuration
        """
        Initializes the InputData class by loading and processing scenario data.

        Args:
            num_samples (int): Number of scenarios for main model training/evaluation.
                               Needs to be >= 2 for P90 model split.
            cv_nsamples (int): Number of scenarios for cross-validation (if used elsewhere).
        """
