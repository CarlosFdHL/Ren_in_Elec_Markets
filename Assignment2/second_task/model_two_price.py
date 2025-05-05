import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt
import numpy as np

from input_data import InputData # Assuming input_data.py is in the same directory or Python path

# A small helper class (can be kept if used for variables/constraints)
class Expando(object):
    ''' A small class which can have attributes set '''
    pass

class TwoPriceBiddingModel():

    def __init__(self, input_data: InputData, verbose: bool = True):
        if not isinstance(input_data, InputData):
            raise TypeError("input_data must be an instance of InputData class")
        if not input_data.scenarios: # Check if scenarios were loaded
             raise ValueError("InputData instance does not contain scenarios. Loading might have failed.")

        if verbose:
            print()
            print('-' * 50)
            print(f'{"TWO PRICE BIDDING MODEL":^50}') # Centered title
            print('-' * 50)

        self.data = input_data
        self.variables = Expando() # Use Expando for vars/constraints if preferred
        self.constraints = Expando()
        self.results = {} # Initialize results as an empty dictionary
        self.verbose = verbose
        self.model = None # Initialize model attribute
        self.build_model()

    def build_variables(self):
        m = self.model # Local alias

        # Bidded production (hourly)
        self.variables.production = {
            t: m.addVar(lb=0, ub=self.data.p_nom, name=f"Production_{t}")
            for t in self.data.T
        }

        # Imbalance variables (hourly, per scenario)
        # Total imbalance = Real Production - Bidded Production
        self.variables.imbalance = {
            (t, w): m.addVar(lb=-self.data.p_nom, ub=self.data.p_nom, name=f"Imbalance_t{t}_w{w}")
            for w in self.data.W for t in self.data.T
        }
        # Upward imbalance component (Real > Bid)
        self.variables.up_imbalance = {
            (t, w): m.addVar(lb=0, ub=self.data.p_nom, name=f"UpImbalance_t{t}_w{w}")
            for t in self.data.T for w in self.data.W
        }
        # Downward imbalance component (Bid > Real)
        self.variables.down_imbalance = {
            (t, w): m.addVar(lb=0, ub=self.data.p_nom, name=f"DownImbalance_t{t}_w{w}")
            for t in self.data.T for w in self.data.W
        }

    def build_constraints(self):
        m = self.model # Local alias

        # PRODUCTION UPPER LIMIT (covered by var bounds)
        # ...

        # IMBALANCE DEFINITION: Total Imbalance = Real - Bid
        self.constraints.imbalance_definition = {
            (t, w): m.addConstr(
                self.variables.imbalance[t, w] ==
                (self.data.scenarios[w]['rp'][t] * self.data.p_nom) - self.variables.production[t],
                name=f"ImbalanceDef_t{t}_w{w}"
            )
            for t in self.data.T for w in self.data.W
        }

        # IMBALANCE DECOMPOSITION: Total Imbalance = Up Imbalance - Down Imbalance
        self.constraints.imbalance_decomposition = {
            (t, w): m.addConstr(
                self.variables.imbalance[t, w] ==
                self.variables.up_imbalance[t, w] - self.variables.down_imbalance[t, w],
                name=f"ImbalanceDecomp_t{t}_w{w}"
            )
            for t in self.data.T for w in self.data.W
        }
        # Note: The objective function (maximization) will ensure that only one of
        # up_imbalance or down_imbalance is non-zero for a given (t, w).

    def build_objective_function(self):
        m = self.model # Local alias

        # Objective: Maximize expected profit across all scenarios
        # Profit = DA Revenue + Imbalance Revenue/Cost (Two-Price Scheme)

        # Two-Price Scheme Logic:
        # If sc=1 (UP system need):
        #   - Generator has UP imbalance (produced more, imb > 0): Paid DA Price * UpImbalance
        #   - Generator has DOWN imbalance (produced less, imb < 0): Pays Penalty Price * DownImbalance [posFactor * DA price]
        # If sc=0 (DOWN system need):
        #   - Generator has UP imbalance (produced more, imb > 0): Pays Penalty Price * UpImbalance [negFactor * DA price]
        #   - Generator has DOWN imbalance (produced less, imb < 0): Paid DA Price * DownImbalance

        self.objective = self.data.prob_scenario * gp.quicksum(
            # DA Revenue for scenario w, time t
            self.data.scenarios[w]['eprice'][t] * self.variables.production[t] +
            # Imbalance Profit/Cost when system needs UP regulation (sc=1)
            self.data.scenarios[w]['sc'][t] * (
                + self.data.scenarios[w]['eprice'][t] * self.variables.up_imbalance[t, w] # Paid DA Price for Up Imb
                - self.data.positiveBalancePriceFactor * self.data.scenarios[w]['eprice'][t] * self.variables.down_imbalance[t, w] # Pay Penalty for Down Imb
            ) +
            # Imbalance Profit/Cost when system needs DOWN regulation (sc=0)
            (1 - self.data.scenarios[w]['sc'][t]) * (
                - self.data.negativeBalancePriceFactor * self.data.scenarios[w]['eprice'][t] * self.variables.up_imbalance[t, w] # Pay Penalty for Up Imb
                + self.data.scenarios[w]['eprice'][t] * self.variables.down_imbalance[t, w] # Paid DA Price for Down Imb
            )
            for t in self.data.T
            for w in self.data.W
        )

        m.setObjective(self.objective, GRB.MAXIMIZE)

    def build_model(self):
        if self.verbose:
            print("\nBuilding Gurobi model...")

        with gp.Env(empty=True) as env: # Use Gurobi environment
             env.setParam('OutputFlag', 0)
             env.start()
             self.model = gp.Model(name="TwoPriceBiddingModel", env=env) # Corrected model name

             if self.verbose: print("Building variables...")
             self.build_variables()

             if self.verbose: print("Building constraints...")
             self.build_constraints()

             if self.verbose: print("Building objective function...")
             self.build_objective_function()

             self.model.update()
             if self.verbose:
                 print(f"Model built: {self.model.NumVars} variables, {self.model.NumConstrs} constraints.")

    def save_results(self):
        if self.model.status != GRB.OPTIMAL:
             print("Warning: Optimization did not reach optimality. Results may be inaccurate.")
             # Initialize results keys with NaN
             self.results['production'] = {t: np.nan for t in self.data.T}
             self.results['imbalance'] = {(t,w): np.nan for t in self.data.T for w in self.data.W}
             self.results['up_imbalance'] = {(t,w): np.nan for t in self.data.T for w in self.data.W}
             self.results['down_imbalance'] = {(t,w): np.nan for t in self.data.T for w in self.data.W}
             self.results['expected_imbalance'] = {t: np.nan for t in self.data.T}
             self.results['profit'] = np.nan
             self.results['profit_da_hourly_expected'] = {t: np.nan for t in self.data.T}
             self.results['profit_imbalance_hourly_expected'] = {t: np.nan for t in self.data.T}
             self.results['profit_per_scenario'] = {w: np.nan for w in self.data.W}
             self.results['expected_real_prod_hourly'] = {t: np.nan for t in self.data.T}
             self.results['avg_bid'] = np.nan
             return # Stop saving if not optimal

        # Saves the results using dictionary keys
        self.results['production'] = { # Use dict key assignment
            t: self.variables.production[t].X
            for t in self.data.T
        }
        self.results['imbalance'] = { # Use dict key assignment
            (t, w): self.variables.imbalance[t, w].X
            for t in self.data.T for w in self.data.W
        }
        self.results['up_imbalance'] = { # Use dict key assignment
            (t, w): self.variables.up_imbalance[t, w].X
            for t in self.data.T for w in self.data.W
        }
        self.results['down_imbalance'] = { # Use dict key assignment
            (t, w): self.variables.down_imbalance[t, w].X
            for t in self.data.T for w in self.data.W
        }
        self.results['expected_imbalance'] = { # Use dict key assignment
            t: self.data.prob_scenario * sum(self.results['imbalance'][t, w] for w in self.data.W)
            for t in self.data.T
        }
        self.results['profit'] = self.model.ObjVal # Use dict key assignment

        self.results['profit_da_hourly_expected'] = { # Use dict key assignment
            t: self.data.prob_scenario * sum(self.data.scenarios[w]['eprice'][t] * self.results['production'][t] for w in self.data.W)
            for t in self.data.T
        }

        profit_imbalance_scenario_hourly = {
            (t, w): self.data.scenarios[w]['sc'][t] * (
                        self.data.scenarios[w]['eprice'][t] * self.results['up_imbalance'][t, w] # Use dict access
                        - self.data.positiveBalancePriceFactor * self.data.scenarios[w]['eprice'][t] * self.results['down_imbalance'][t, w] # Use dict access
                      ) + \
                      (1 - self.data.scenarios[w]['sc'][t]) * (
                        - self.data.negativeBalancePriceFactor * self.data.scenarios[w]['eprice'][t] * self.results['up_imbalance'][t, w] # Use dict access
                        + self.data.scenarios[w]['eprice'][t] * self.results['down_imbalance'][t, w] # Use dict access
                      )
            for t in self.data.T
            for w in self.data.W
        }

        self.results['profit_imbalance_hourly_expected'] = { # Use dict key assignment
             t: self.data.prob_scenario * sum(profit_imbalance_scenario_hourly[t, w] for w in self.data.W)
             for t in self.data.T
        }

        self.results['profit_per_scenario'] = { # Use dict key assignment
             w: sum( self.data.scenarios[w]['eprice'][t] * self.results['production'][t] + profit_imbalance_scenario_hourly[t,w]
                     for t in self.data.T)
             for w in self.data.W
        }

        self.results['expected_real_prod_hourly'] = { # Use dict key assignment
            t: self.data.prob_scenario * sum(self.data.scenarios[w]['rp'][t] * self.data.p_nom for w in self.data.W)
            for t in self.data.T
        }

        total_production_bid = sum(self.results['production'].values())
        self.results['avg_bid'] = total_production_bid / len(self.data.T) if self.data.T else 0 # Use dict key assignment


    def print_results(self):
        # Access results using dictionary keys
        if not self.results or 'profit' not in self.results or np.isnan(self.results['profit']): # Check dict/key
             print("Results not available or model was not solved optimally.")
             return

        print('\n' + '-' * 50)
        print(f'{"TWO PRICE MODEL - RESULTS SUMMARY":^50}')
        print('-' * 50)

        print(f"Total Expected Profit: {self.results['profit']:.2f} €")
        print(f"Average Hourly Bid: {self.results['avg_bid']:.2f} kW")
        print('-' * 50)

        # --- Hourly Production Bids ---
        print(f'{"Hourly Production Bids (kW)":^50}')
        print(f'{"Hour":^10} {"Bid (kW)":^20} {"Exp. Real Prod (kW)":^20}')
        print('-' * 50)
        for t in self.data.T:
            print(f'{t:^10} {self.results["production"][t]:^20.2f} {self.results["expected_real_prod_hourly"][t]:^20.2f}')
        print('-' * 50)

        # --- Hourly Expected Profits ---
        print(f'{"Hourly Expected Profits (€)":^50}')
        print(f'{"Hour":^10} {"DA Profit":^15} {"Imbalance Profit":^15} {"Total Profit":^15}')
        print('-' * 50)
        total_profit_check = 0
        for t in self.data.T:
            da_prof = self.results['profit_da_hourly_expected'][t]
            imb_prof = self.results['profit_imbalance_hourly_expected'][t]
            total_hourly = da_prof + imb_prof
            total_profit_check += total_hourly
            print(f'{t:^10} {da_prof:^15.2f} {imb_prof:^15.2f} {total_hourly:^15.2f}')
        print('-' * 50)
        print(f'{"Sum of Hourly Exp. Profits:":<35} {total_profit_check:>15.2f} €')
        print(f'{"Model Objective Value:":<35} {self.results["profit"]:>15.2f} €')
        print('-' * 50)

    def plot(self):
        # Access results using dictionary keys
        if not self.results or 'profit' not in self.results or np.isnan(self.results['profit']): # Check dict/key
             print("Cannot plot results: Results not available or model not solved optimally.")
             return

        fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(14, 10))
        fig.suptitle('Two-Price Model Analysis', fontsize=16) # Changed title

        hours = self.data.T
        exp_profit_da = [self.results['profit_da_hourly_expected'].get(t, 0) for t in hours]
        exp_profit_imb = [self.results['profit_imbalance_hourly_expected'].get(t, 0) for t in hours]
        exp_total_profit = [p_da + p_imb for p_da, p_imb in zip(exp_profit_da, exp_profit_imb)]
        bids = [self.results['production'].get(t, 0) for t in hours]
        exp_real_prod = [self.results['expected_real_prod_hourly'].get(t, 0) for t in hours]
        exp_imbalance = [self.results['expected_imbalance'].get(t, 0) for t in hours]
        profit_per_scenario_values = list(self.results['profit_per_scenario'].values())

        # Plot 1: Hourly Expected Profits
        ax[0, 0].plot(hours, exp_profit_da, label='Exp. DA Profit', color='blue', marker='x', linestyle='--')
        ax[0, 0].plot(hours, exp_profit_imb, label='Exp. Imbalance Profit', color='red', marker='o', linestyle='-.')
        ax[0, 0].plot(hours, exp_total_profit, color='black', label='Total Exp. Profit', marker='.')
        ax[0, 0].set_ylabel('Expected Profit (€)')
        ax[0, 0].set_xlabel('Time (h)')
        ax[0, 0].set_title('Hourly Expected Profits')
        ax[0, 0].legend()
        ax[0, 0].grid(True)

        # Plot 2: Hourly Bids vs Expected Real Production
        ax[0, 1].plot(hours, bids, label='Bid (kW)', color='green', marker='s', linestyle='-')
        ax[0, 1].plot(hours, exp_real_prod, label='Exp. Real Prod (kW)', color='purple', marker='^', linestyle=':')
        ax[0, 1].set_ylabel('Power (kW)')
        ax[0, 1].set_xlabel('Time (h)')
        ax[0, 1].set_title('Hourly Bids vs Expected Production')
        ax[0, 1].legend()
        ax[0, 1].grid(True)

        # Plot 3: Profit Distribution Histogram
        ax[1, 0].hist(profit_per_scenario_values, bins=30, alpha=0.75, color='lightcoral', edgecolor='black') # Changed color
        ax[1, 0].set_title('Distribution of Profit Per Scenario')
        ax[1, 0].set_xlabel('Total Profit per Scenario (€)')
        ax[1, 0].set_ylabel('Number of Scenarios')
        ax[1, 0].grid(True)
        mean_profit = np.mean(profit_per_scenario_values)
        ax[1, 0].axvline(mean_profit, color='blue', linestyle='dashed', linewidth=1) # Changed color
        ax[1, 0].text(mean_profit*1.1, ax[1,0].get_ylim()[1]*0.9, f'Mean: {mean_profit:.2f}', color='blue') # Changed color

        # Plot 4: Expected Hourly Imbalance
        ax[1, 1].bar(hours, exp_imbalance, color='gold', label='Exp. Imbalance (kW)') # Changed color
        ax[1, 1].set_ylabel('Expected Imbalance (kW)')
        ax[1, 1].set_xlabel('Time (h)')
        ax[1, 1].set_title('Expected Hourly Imbalance (Real - Bid)')
        ax[1, 1].axhline(0, color='black', linewidth=0.5)
        ax[1, 1].grid(axis='y')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        # Consider saving the plot from main script instead of showing here
        # plt.show()


    def run(self):
        # Identical structure to OnePriceBiddingModel's run method
        if not self.model:
            print("Error: Model was not built successfully.")
            return

        try:
            if self.verbose: print("\nOptimizing model...")
            self.model.optimize()
            # self.model.write("two_price_model.lp") # Optional: write LP file

            if self.model.status == GRB.OPTIMAL:
                if self.verbose:
                    print("Optimization successful!")
                    print(f"Optimal Objective Value: {self.model.ObjVal:.2f} €")
                self.save_results()
                # self.plot() # Optionally plot after run
            elif self.model.status == GRB.INFEASIBLE:
                print("Error: Model is infeasible.")
                print("Computing IIS...")
                self.model.computeIIS()
                self.model.write("two_price_model_infeasible.ilp")
                print("IIS written to two_price_model_infeasible.ilp")
                self.save_results() # Save NaNs
            elif self.model.status == GRB.UNBOUNDED:
                print("Error: Model is unbounded.")
                self.save_results() # Save NaNs
            else:
                print(f"Optimization finished with status code: {self.model.status}")
                self.save_results() # Save NaNs

        except gp.GurobiError as e:
            print(f"Gurobi Error code {e.errno}: {e}")
            self.save_results() # Save NaNs
        except Exception as e:
             print(f"An unexpected error occurred during optimization: {e}")
             self.save_results() # Save NaNs