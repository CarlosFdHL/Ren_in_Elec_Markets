import numpy as np
import pandas as pd
from typing import Dict, List
from input_data import InputData # Assuming input_data.py is available

class P90BiddingModel:
    def __init__(self, input_data: InputData, verbose: bool = True):
        """
        Initialize P90 bidding model.

        Args:
            input_data: InputData class instance containing scenarios and parameters.
            verbose: Whether to print progress messages.
        """

        self.data = input_data
        self.verbose = verbose
        self.results = {} # Initialize results as an empty dictionary

        # Split scenarios
        all_scenario_keys = sorted(list(self.data.scenarios.keys())) # Sort keys for consistency

        in_sample_keys = all_scenario_keys[:100]
        out_sample_keys = all_scenario_keys[200:]

        self.in_sample_scenarios = {k: self.data.scenarios[k] for k in in_sample_keys}
        self.out_sample_scenarios = {k: self.data.scenarios[k] for k in out_sample_keys}



