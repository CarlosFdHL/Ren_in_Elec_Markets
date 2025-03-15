import numpy as np
import pandas as pd

class InputDataRegulation:
    def __init__(self, input_data_day_ahead):

        self.offers_regulation = input_data_day_ahead.data.offers_regulation

        self.variation = {
            (g, t): input_data_day_ahead.results.production_data.at[t, g] * input_data_day_ahead.data.variation[g]
            for g in input_data_day_ahead.data.generators
            for t in input_data_day_ahead.data.timeSpan
        }
        print(self.variation)
        self.balance = {
            t: sum(self.variation[g,t] for g in input_data_day_ahead.data.generators)
            for t in input_data_day_ahead.data.timeSpan
        }
        print("Balance : ",self.balance)

        for g in input_data_day_ahead.data.generators:
            for t in input_data_day_ahead.data.timeSpan:
                if self.variation[g, t] * self.balance[t] > 0: # If the generator is producing the system imbalance
                    self.offers_regulation[g] = False

        self.up_regulation_max = {
            (g, t): (input_data_day_ahead.data.Pmax[g] - (input_data_day_ahead.results.production_data.at[t, g] + self.variation[g, t])) * self.offers_regulation[g]
            for g in input_data_day_ahead.data.generators if self.offers_regulation[g] == True
            for t in input_data_day_ahead.data.timeSpan
        }
        print("!!!!",self.offers_regulation)
        print("!!!!",self.up_regulation_max)

        self.down_regulation_max = {
            (g, t): (input_data_day_ahead.results.production_data.at[t, g] + self.variation[g, t]) * self.offers_regulation[g]
            for g in input_data_day_ahead.data.generators if self.offers_regulation[g] == True
            for t in input_data_day_ahead.data.timeSpan
        }

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