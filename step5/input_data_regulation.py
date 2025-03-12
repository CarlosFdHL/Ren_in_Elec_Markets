import numpy as np
import pandas as pd

class InputDataRegulation:
    def __init__(self, input_data_day_ahead):

        self.up_regulation_max = {
            (g, t): (input_data_day_ahead.data.Pmax[g] - input_data_day_ahead.results.production_data.at[t, g]) * input_data_day_ahead.data.offers_regulation[g]
            for g in input_data_day_ahead.data.generators if input_data_day_ahead.data.wind[g] == False
            for t in input_data_day_ahead.data.timeSpan
        }
        self.down_regulation_max = {
            (g, t): input_data_day_ahead.results.production_data.at[t, g] * input_data_day_ahead.data.offers_regulation[g]
            for g in input_data_day_ahead.data.generators
            for t in input_data_day_ahead.data.timeSpan
        }
        self.variation = {
            (g,t): input_data_day_ahead.results.production_data.at[t, g] * (1 + input_data_day_ahead.data.variation[g])
            for g in input_data_day_ahead.data.generators
            for t in input_data_day_ahead.data.timeSpan
        }
        self.upward_regulation_bid = {
            (g,t): input_data_day_ahead.results.price[t] + 0.1 * input_data_day_ahead.data.bid_offers[g]
            for g in input_data_day_ahead.data.generators
            for t in input_data_day_ahead.data.timeSpan
        }
        self.downward_regulation_bid = {
            (g,t): input_data_day_ahead.results.price[t] - 0.15 * input_data_day_ahead.data.bid_offers[g]
            for g in input_data_day_ahead.data.generators
            for t in input_data_day_ahead.data.timeSpan
        }