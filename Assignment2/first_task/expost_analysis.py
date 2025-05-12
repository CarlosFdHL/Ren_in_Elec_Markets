import numpy as np
import pandas as pd
from sklearn.model_selection import KFold


from .input_data import InputData
from .model_one_price import OnePriceBiddingModel
from .model_two_price import TwoPriceBiddingModel

class ExPostAnalysis:
    def __init__(self, scenarios: list, indices: list, timeSpan: list, model_type: str, num_folds: int = 8, verbose: bool = True):
        self.K = num_folds
        self.scenarios = scenarios
        self.W = list(range(1, len(scenarios)+1))
        self.n_scenarios = len(self.W)
        self.T = timeSpan
        self.model_type = model_type
        self.verbose = verbose

        # Store the model class, not an instance
        if self.model_type == 'one_price':
            self.model_class = OnePriceBiddingModel
        elif self.model_type == 'two_price':
            self.model_class = TwoPriceBiddingModel
        else:
            raise ValueError("Invalid model type. Use 'one_price' or 'two_price'.")
        
    def insample_analysis(self, scenarios, indices):
        # Create an instance of InputData
        input_data = InputData(T = self.T, W = indices, scenario = scenarios, prob_scenario = 1/len(scenarios), model_type = self.model_type)
        
        # Initialize the model with the input data
        model = self.model_class(input_data, verbose=self.verbose)

        # Run the model
        model.run()

        return model, model.results.profit_da, model.results.profit 

    def outsample_analysis(self, model, scenarios):
        # Calculate the profit from DA market
        profit_da = {
            t: model.results.production[t] * sum(scenarios[w]['eprice'][t] for w in scenarios.keys()) / len(scenarios)
            for t in model.data.T
        }
        total_profit_da = sum(profit_da.values())
        # Calculate the imbalance for the out-of-sample scenarios. This imbalance is the same for one or two price schemes.
        imbalance = {
            (t, w): scenarios[w]['rp'][t] * model.data.p_nom - model.results.production[t] 
            for t in model.data.T 
            for w in scenarios.keys()
        }

        if self.model_type == 'one_price':
            # If we are under a one price scheme, we calculate the imbalance profit as follows:
            imbalance_profit = {
                (t, w): model.data.positiveBalancePriceFactor * scenarios[w]['eprice'][t] * imbalance[t, w] * scenarios[w]['sc'][t]  +
                    model.data.negativeBalancePriceFactor * scenarios[w]['eprice'][t] * imbalance[t,w] * (1 - scenarios[w]['sc'][t])
                    for t in model.data.T
                    for w in scenarios.keys()
            }

        elif self.model_type == 'two_price':
            # Calculate up and down imbalance for the out of sample scenarios    
            up_imbalance = {}
            down_imbalance = {}
            for w in scenarios.keys() :
                for t in self.T:
                    # The imbalance has to be the difference between the up and down imbalance and one of them has to be zero
                    if imbalance[t, w] > 0:
                        up_imbalance[t, w] = imbalance[t, w]
                        down_imbalance[t, w] = 0
                    else:
                        up_imbalance[t, w] = 0
                        down_imbalance[t, w] = -imbalance[t, w]
            # If we are under a two price scheme, we calculate the imbalance profit as follows:
            imbalance_profit = {
                (t,w): scenarios[w]['sc'][t] * (scenarios[w]['eprice'][t] * up_imbalance[t,w]
                        - model.data.positiveBalancePriceFactor * scenarios[w]['eprice'][t] * down_imbalance[t,w])                                 # Profit from imbalance in case of system requiring upward balance
                        + (1 - scenarios[w]['sc'][t]) * (model.data.negativeBalancePriceFactor * scenarios[w]['eprice'][t] * up_imbalance[t,w]
                        - scenarios[w]['eprice'][t] * down_imbalance[t,w])                                                                         # Profit from imbalance in case of system requiring downward balance
                    for t in model.data.T
                    for w in scenarios.keys()
            }
        else:
            raise ValueError("Invalid model type. Use 'one_price' or 'two_price'.")

        # Expected imbalance is the sum of the products of the probability of the scenario and the imbalance
        expected_imbalance = {
            t: sum(imbalance[t, w] for w in scenarios.keys()) /len(scenarios)
            for t in model.data.T
        }

        # Expected profit imbalance is the sum of the products of the probability of the scenario and the profit from imbalance
        expected_profit_imbalance = {
            t: sum(imbalance_profit[t, w] for w in scenarios.keys()) /len(scenarios)
            for t in model.data.T
        }

        total_expected_imbalance = sum(expected_imbalance.values()) # Sum over all time periods
        total_expected_profit_imbalance = sum(expected_profit_imbalance.values()) # Sum over all time periods

        return total_expected_imbalance, total_expected_profit_imbalance, total_profit_da


    def cross_validation(self, K):
        kf = KFold(n_splits=K, shuffle=False)
        indices_array = np.array(self.W)

        results = []

        for i, (out_index, in_index) in enumerate(kf.split(indices_array)):
            if self.verbose:
                print(f"\n=== FOLD {i}/{self.K} ===")
                print(f"In-sample scenarios: {len(in_index)} | Out-of-sample scenarios: {len(out_index)}")

            # Convert indices to scenario keys (they start from 1)
            in_indices = indices_array[in_index]
            out_indices = indices_array[out_index]

            in_scenarios = {w: self.scenarios[w] for w in in_indices}
            out_scenarios = {w: self.scenarios[w] for w in out_indices}

            # Step 1: solve insample
            model, profit_da, insample_expected_profit = self.insample_analysis(
                scenarios=in_scenarios,
                indices=in_indices
            )
            # Step 2: evaluate out-of-sample
            outsample_expected_imbalance, outsample_expected_profit_imbalance, outsample_profit_da = self.outsample_analysis(
                model=model,
                scenarios=out_scenarios
            )

            outofsample_expected_profit = outsample_profit_da + outsample_expected_profit_imbalance
            profit_difference = insample_expected_profit - outofsample_expected_profit

            if self.verbose:
                print(f"In-sample profit DA: {round(sum(profit_da.values()), 1)}")
                print(f"In-sample total expected profit: {round(insample_expected_profit, 1)}")
                print(f"Out-sample expected imbalance: {round(outsample_expected_imbalance, 1)}")
                print(f"Out-sample expected profit imbalance: {round(outsample_expected_profit_imbalance, 1)}")
                print()
                print(f"="*8)
                print(f"In-sample expected profit: {round(insample_expected_profit, 1)}")
                print(f"Out-sample expected profit: {round(outofsample_expected_profit, 1)}")
                print(f"Profit difference: {round(profit_difference, 1)}")
                #print(f"Relative difference: {round(profit_difference / insample_expected_profit * 100, 1)}%")
                print(f"="*8)

            results.append({
                "fold": i,
                "profit_da": profit_da,
                "insample_expected_profit": insample_expected_profit,
                "outofsample_expected_profit": outofsample_expected_profit,
                "expected_profit_difference": profit_difference,
                "expected_relative_difference": profit_difference / insample_expected_profit * 100,
            })
        
        if self.verbose:
            print(f"\n=== RESULTS SUMMARY ===")
            # Average of results accross all folds
            profit_da_df = pd.DataFrame([result["profit_da"] for result in results])
            avg_profit_da = profit_da_df.mean(axis=0)        
            avg_insample_profit = np.mean([float(result["insample_expected_profit"]) for result in results])
            avg_outofsample_profit = np.mean([float(result["outofsample_expected_profit"]) for result in results])
            avg_difference = np.mean([float(result["expected_profit_difference"]) for result in results])
            avg_relative_difference = np.mean([float(result["expected_relative_difference"]) for result in results])

            print(f"Average in-sample profit DA: {round(avg_profit_da.sum(), 1)}")
            print(f"Average in-sample expected profit: {round(avg_insample_profit, 1)}")
            #print(f"Average out-of-sample expected profit from imbalance: {round(avg_outofsample_profit, 1)}")
            print(f"Average out-of-sample expected profit: {round(avg_outofsample_profit, 1)}")
            #print(f"Average profit difference: {round(avg_difference, 1)}")
            #print(f"Average relative difference: {round(avg_relative_difference, 1)}%")
            print(f"Difference of the average between in-sample and out-of-sample expected profit: {round(avg_insample_profit - avg_outofsample_profit, 1)}")
            print(f"Relative difference of the average between in-sample and out-of-sample expected profit: {round((avg_insample_profit - avg_outofsample_profit) / avg_insample_profit * 100, 1)}%")
            print(f"{'='*30}")
        return results

