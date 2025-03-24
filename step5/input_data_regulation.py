import numpy as np
import pandas as pd
'''
This file contains the InputDataRegulation class that is used to store the technical data for each generator and the system demand data for the regulation market.
'''
class InputDataRegulation:
    def __init__(self, input_data_day_ahead):

        # If the generator is producing the system imbalance, it cannot offer regulation
        self.offers_regulation = input_data_day_ahead.data.offers_regulation

        # System imbalance
        self.variation = {
            (g, t): input_data_day_ahead.results.production_data.at[t, g] * input_data_day_ahead.data.variation[g]
            for g in input_data_day_ahead.data.generators
            for t in input_data_day_ahead.data.timeSpan
        }
        self.imbalance = {
            t: sum(self.variation[g,t] for g in input_data_day_ahead.data.generators)
            for t in input_data_day_ahead.data.timeSpan
        }

        for g in input_data_day_ahead.data.generators:
            for t in input_data_day_ahead.data.timeSpan:
                if self.variation[g, t] * self.imbalance[t] > 0: # If the generator is producing the system imbalance
                    self.offers_regulation[g] = False
        
        # Maximum up regulation capacity
        self.up_regulation_max = {
            (g, t): (input_data_day_ahead.data.Pmax[g] - (input_data_day_ahead.results.production_data.at[t, g] + self.variation[g, t])) * self.offers_regulation[g]
            for g in input_data_day_ahead.data.generators if self.offers_regulation[g] == True
            for t in input_data_day_ahead.data.timeSpan
        }

        # Maximum down regulation capacity
        self.down_regulation_max = {
            (g, t): (input_data_day_ahead.results.production_data.at[t, g] + self.variation[g, t]) * self.offers_regulation[g]
            for g in input_data_day_ahead.data.generators if self.offers_regulation[g] == True
            for t in input_data_day_ahead.data.timeSpan
        }

        # Regulation bid prices for the regulation market
        self.upward_regulation_bid = {
            (g,t): input_data_day_ahead.results.price[t] + 0.1 * input_data_day_ahead.data.bid_offers[g]
            for g in input_data_day_ahead.data.generators if self.offers_regulation[g] == True
            for t in input_data_day_ahead.data.timeSpan
        }
        self.downward_regulation_bid = {
            (g,t): input_data_day_ahead.results.price[t] - 0.15 * input_data_day_ahead.data.bid_offers[g]
            for g in input_data_day_ahead.data.generators if self.offers_regulation[g] == True
            for t in input_data_day_ahead.data.timeSpan
        }