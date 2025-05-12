import numpy as np
import pandas as pd
from sklearn.model_selection import ShuffleSplit


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
        input_data = InputData(self.T, indices, scenarios, 1/len(scenarios))
        
        # Initialize the model with the input data
        model = self.model_class(input_data, verbose=self.verbose)

        # Run the model
        model.run()

        return model, model.results.profit_da, model.results.profit 

    def outsample_analysis(self, model, scenarios):


        if model.data.model_type == 'two_price':
            imbalance = {
                (t, w): scenarios[w]['rp'][t] * model.data.p_nom - model.results.production[t] 
                for t in model.data.T 
                for w in scenarios.keys()
            }
            imbalance_profit = {
                (t, w): model.data.positiveBalancePriceFactor * scenarios[w]['eprice'][t] * imbalance[t, w] * scenarios[w]['sc'][t]  +
                    model.data.negativeBalancePriceFactor * scenarios[w]['eprice'][t] * imbalance[t,w] * (1 - scenarios[w]['sc'][t])
                    for t in model.data.T
                    for w in scenarios.keys()
            }
        elif model.data.model_type == 'one_price':
            print("One price model:", model.data.model_type)
            imbalance_profit = {
                (t,w): scenarios[w]['sc'][t] * (scenarios[w]['eprice'][t] * model.variables.up_imbalance[t,w].X 
                        - model.data.positiveBalancePriceFactor * scenarios[w]['eprice'][t] * model.variables.down_imbalance[t,w].X)                                            # Profit from imbalance in case of system requiring upward balance
                        + (1 - scenarios[w]['sc'][t]) * (model.data.negativeBalancePriceFactor * scenarios[w]['eprice'][t] * model.variables.up_imbalance[t,w].X 
                        - model.data.scenario[w]['eprice'][t] * self.variables.down_imbalance[t,w].X)                                                                           # Profit from imbalance in case of system requiring downward balance
                    for t in model.data.T
                    for w in model.data.W
            }
        else:
            raise ValueError("Invalid model type. Use 'one_price' or 'two_price'.")

        expected_imbalance = {
            t: sum(imbalance[t, w] for w in scenarios.keys()) / len(scenarios)
            for t in model.data.T
        }

        expected_profit_imbalance = {
            t: sum(imbalance_profit[t, w] for w in scenarios.keys()) / len(scenarios)
            for t in model.data.T
        }

        total_expected_imbalance = sum(expected_imbalance.values())
        total_expected_profit_imbalance = sum(expected_profit_imbalance.values())

        return total_expected_imbalance, total_expected_profit_imbalance


    def cross_validation(self, insample_size: int = 200, outsample_size: int = 1400):
        ss = ShuffleSplit(n_splits=self.K, test_size=insample_size, train_size=outsample_size, random_state=42)
        indices_array = np.array(self.W)

        results = []

        for i, (out_index, in_index) in enumerate(ss.split(indices_array), start=1):
            if self.verbose:
                print(f"\n=== FOLD {i}/{self.K} ===")
                print(f"In-sample scenarios: {len(in_index)} | Out-of-sample scenarios: {len(out_index)}")

            # Convert indices to scenario keys (they start from 1)
            in_indices = indices_array[in_index]
            out_indices = indices_array[out_index]

            in_scenarios = {w: self.scenarios[w] for w in in_indices}
            out_scenarios = {w: self.scenarios[w] for w in out_indices}

            # Step 1: solve insample
            model, profit_da, profit_total = self.insample_analysis(
                scenarios=in_scenarios,
                indices=in_indices
            )
            insample_profit = profit_total

            print("!!!!!!", model.data.model_type)

            # Step 2: evaluate out-of-sample
            expected_imbalance, expected_profit_imbalance = self.outsample_analysis(
                model=model,
                scenarios=out_scenarios
            )
            outofsample_profit = sum(profit_da.values()) + expected_profit_imbalance
            profit_difference = insample_profit - outofsample_profit

            if self.verbose:
                print(f"In-sample profit DA: {round(sum(profit_da.values()), 1)}")
                print(f"In-sample total profit: {round(profit_total, 1)}")
                print(f"Out-sample expected imbalance: {round(expected_imbalance, 1)}")
                print(f"Out-sample expected profit imbalance: {round(expected_profit_imbalance, 1)}")
                print()
                print(f"="*8)
                print(f"In-sample expected profit: {round(insample_profit, 1)}")
                print(f"Out-sample expected profit: {round(outofsample_profit, 1)}")
                print(f"Profit difference: {round(profit_difference, 1)}")
                print(f"Relative difference: {round(profit_difference / insample_profit * 100, 1)}%")
                print(f"="*8)

            results.append({
                "fold": i,
                "profit_da": profit_da,
                "insample_profit": insample_profit,
                "outofsample_profit": outofsample_profit,
                "difference": profit_difference,
                "relative_difference": profit_difference / insample_profit * 100,
            })
        
        if self.verbose:
            print(f"\n=== RESULTS SUMMARY ===")
            # Average of results accross all folds
            profit_da_df = pd.DataFrame([result["profit_da"] for result in results])
            avg_profit_da = profit_da_df.mean(axis=0)        
            avg_insample_profit = np.mean([float(result["insample_profit"]) for result in results])
            avg_outofsample_profit = np.mean([float(result["outofsample_profit"]) for result in results])
            avg_difference = np.mean([float(result["difference"]) for result in results])
            avg_relative_difference = np.mean([float(result["relative_difference"]) for result in results])

            print(f"Average in-sample profit DA: {round(avg_profit_da.sum(), 1)}")
            print(f"Average in-sample total profit: {round(avg_insample_profit, 1)}")
            print(f"Average out-of-sample expected profit from imbalance: {round(avg_outofsample_profit, 1)}")
            print(f"Average in-sample expected profit: {round(avg_insample_profit, 1)}")
            print(f"Average out-of-sample expected profit: {round(avg_outofsample_profit, 1)}")
            print(f"Average profit difference: {round(avg_difference, 1)}")
            print(f"Average relative difference: {round(avg_relative_difference, 1)}%")
            print(f"{'='*30}")
        return results

