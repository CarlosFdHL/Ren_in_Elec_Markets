import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt
import numpy as np

# Plotting parameters (optional, consider moving to plotting.py or main script)
# plt.rcParams['font.family'] = 'serif'
# plt.rcParams['font.size'] = 14

from input_data import InputData # Assuming input_data.py is in the same directory or Python path

# A small helper class (can be kept if used for variables/constraints)
class Expando(object):
    ''' A small class which can have attributes set '''
    pass

class OnePriceBiddingModel():

    def __init__(self, input_data: InputData, verbose: bool = True):
        if not isinstance(input_data, InputData):
            raise TypeError("input_data must be an instance of InputData class")
        if not input_data.scenarios: # Check if scenarios were loaded
             raise ValueError("InputData instance does not contain scenarios. Loading might have failed.")

        if verbose:
            print()
            print('-' * 50)
            print(f'{"ONE PRICE BIDDING MODEL":^50}') # Centered title
            print('-' * 50)

        self.data = input_data
        self.variables = Expando() # Use Expando for vars/constraints if preferred
        self.constraints = Expando()
        self.results = {} # Initialize results as an empty dictionary
        self.verbose = verbose
        self.model = None # Initialize model attribute
        self.build_model()

    def build_variables(self):
        m = self.model # Local alias for model

        # Bidded production (hourly)
        self.variables.production = {
            t: m.addVar(lb=0, ub=self.data.p_nom, name=f"Production_{t}") # Added upper bound
            for t in self.data.T
        }

        # Imbalance of the generator (hourly, per scenario)
        # Bounds can be tightened: max possible imbalance is p_nom
        self.variables.imbalance = {
            (t, w): m.addVar(lb=-self.data.p_nom, ub=self.data.p_nom, name=f"Imbalance_t{t}_w{w}")
            for w in self.data.W
            for t in self.data.T
        }

    def build_constraints(self):
        m = self.model # Local alias

        # PRODUCTION UPPER LIMIT (already included in variable bounds, but explicit constraint is fine too)
        # self.constraints.production_upper_limit = {
        #     t: m.addConstr(self.variables.production[t] <= self.data.p_nom, name=f"ProdUpperLimit_{t}")
        #     for t in self.data.T
        # }

        # IMBALANCE DEFINITION
        # Imbalance = Real Production - Bidded Production
        # Real Production = Rate of Production (%) * Nominal Power (kW)
        self.constraints.imbalance_definition = {
            (t, w): m.addConstr(
                self.variables.imbalance[t, w] ==
                (self.data.scenarios[w]['rp'][t] * self.data.p_nom) - self.variables.production[t],
                name=f"ImbalanceDef_t{t}_w{w}"
            )
            for t in self.data.T
            for w in self.data.W
        }

    def build_objective_function(self):
        m = self.model # Local alias

        # Objective: Maximize expected profit across all scenarios
        # Profit = DA Revenue + Imbalance Revenue/Cost

        # DA Revenue = DA Price * Bidded Production
        # Imbalance Revenue/Cost depends on system condition (sc) and imbalance direction
        # System condition sc[t] = 1 means system needs UP regulation (deficit)
        # System condition sc[t] = 0 means system needs DOWN regulation (surplus)
        # Imbalance > 0 (Upward) means Generator Produced MORE than bid
        # Imbalance < 0 (Downward) means Generator Produced LESS than bid

        # One-Price Scheme Logic:
        # - If sc=1 (UP): Paid for positive imbalance, pay for negative imbalance at imbalance price (posFactor * DAprice)
        # - If sc=0 (DOWN): Pay for positive imbalance, paid for negative imbalance at imbalance price (negFactor * DAprice)
        # --> Simplified: Profit = DAprice*Prod + ImbPrice * Imbalance
        #     where ImbPrice = posFactor*DAprice if sc=1, negFactor*DAprice if sc=0

        self.objective = self.data.prob_scenario * gp.quicksum(
            # DA Revenue for scenario w, time t (Price depends on scenario)
            self.data.scenarios[w]['eprice'][t] * self.variables.production[t] +
            # Imbalance Revenue/Cost for scenario w, time t
            ( self.data.scenarios[w]['sc'][t] * self.data.positiveBalancePriceFactor * self.data.scenarios[w]['eprice'][t] * self.variables.imbalance[t, w] ) +
            ( (1 - self.data.scenarios[w]['sc'][t]) * self.data.negativeBalancePriceFactor * self.data.scenarios[w]['eprice'][t] * self.variables.imbalance[t, w] )
            for t in self.data.T
            for w in self.data.W
        )

        m.setObjective(self.objective, GRB.MAXIMIZE)

    def build_model(self):
        if self.verbose:
            print("\nBuilding Gurobi model...")

        # Environment context manager is recommended
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag', 0) # Suppress Gurobi output
            env.start()
            # Create the model within the environment
            self.model = gp.Model(name="OnePriceBiddingModel", env=env)

            if self.verbose: print("Building variables...")
            self.build_variables()

            if self.verbose: print("Building constraints...")
            self.build_constraints()

            if self.verbose: print("Building objective function...")
            self.build_objective_function()

            self.model.update() # Update model structure
            if self.verbose:
                print(f"Model built: {self.model.NumVars} variables, {self.model.NumConstrs} constraints.")

    def save_results(self):
        if self.model.status != GRB.OPTIMAL:
             print("Warning: Optimization did not reach optimality. Results may be inaccurate.")
             # Initialize results keys with NaN
             self.results['production'] = {t: np.nan for t in self.data.T}
             self.results['imbalance'] = {(t,w): np.nan for t in self.data.T for w in self.data.W}
             self.results['expected_imbalance'] = {t: np.nan for t in self.data.T}
             self.results['profit'] = np.nan
             self.results['profit_da_hourly_expected'] = {t: np.nan for t in self.data.T}
             self.results['profit_imbalance_hourly_expected'] = {t: np.nan for t in self.data.T}
             self.results['profit_per_scenario'] = {w: np.nan for w in self.data.W}
             self.results['expected_real_prod_hourly'] = {t: np.nan for t in self.data.T}
             self.results['avg_bid'] = np.nan
             return # Stop saving if not optimal

        # Saves the results of the model using dictionary keys
        self.results['production'] = { # Use dict key assignment
            t: self.variables.production[t].X
            for t in self.data.T
        }
        self.results['imbalance'] = { # Use dict key assignment
            (t, w): self.variables.imbalance[t, w].X
            for t in self.data.T
            for w in self.data.W
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
            (t, w): ( self.data.scenarios[w]['sc'][t] * self.data.positiveBalancePriceFactor * self.data.scenarios[w]['eprice'][t] * self.results['imbalance'][t, w] ) +
                      ( (1 - self.data.scenarios[w]['sc'][t]) * self.data.negativeBalancePriceFactor * self.data.scenarios[w]['eprice'][t] * self.results['imbalance'][t, w] )
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
        print(f'{"ONE PRICE MODEL - RESULTS SUMMARY":^50}')
        print('-' * 50)

        print(f"Total Expected Profit: {self.results['profit']:.2f} €")
        print(f"Average Hourly Bid: {self.results['avg_bid']:.2f} kW") # Changed unit label to kW
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
        # Define figure
        # Access results using dictionary keys
        if not self.results or 'profit' not in self.results or np.isnan(self.results['profit']): # Check dict/key
             print("Cannot plot results: Results not available or model not solved optimally.")
             return

        fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(14, 10)) # Adjusted layout
        fig.suptitle('One-Price Model Analysis', fontsize=16)

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
        ax[1, 0].hist(profit_per_scenario_values, bins=30, alpha=0.75, color='skyblue', edgecolor='black')
        ax[1, 0].set_title('Distribution of Profit Per Scenario')
        ax[1, 0].set_xlabel('Total Profit per Scenario (€)')
        ax[1, 0].set_ylabel('Number of Scenarios')
        ax[1, 0].grid(True)
        mean_profit = np.mean(profit_per_scenario_values)
        ax[1, 0].axvline(mean_profit, color='red', linestyle='dashed', linewidth=1)
        ax[1, 0].text(mean_profit*1.1, ax[1,0].get_ylim()[1]*0.9, f'Mean: {mean_profit:.2f}', color='red')


        # Plot 4: Expected Hourly Imbalance
        ax[1, 1].bar(hours, exp_imbalance, color='orange', label='Exp. Imbalance (kW)')
        ax[1, 1].set_ylabel('Expected Imbalance (kW)')
        ax[1, 1].set_xlabel('Time (h)')
        ax[1, 1].set_title('Expected Hourly Imbalance (Real - Bid)')
        ax[1, 1].axhline(0, color='black', linewidth=0.5)
        ax[1, 1].grid(axis='y')


        plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to prevent title overlap
        # Consider saving the plot from main script instead of showing here
        # plt.show()


    def run(self):
        if not self.model:
            print("Error: Model was not built successfully.")
            return

        try:
            if self.verbose: print("\nOptimizing model...")
            self.model.optimize()
            # self.model.write("one_price_model.lp") # Optional: write LP file

            if self.model.status == GRB.OPTIMAL:
                if self.verbose:
                    print("Optimization successful!")
                    print(f"Optimal Objective Value: {self.model.ObjVal:.2f} €")
                self.save_results()
                # Optionally call plot here if desired after run()
                # self.plot()
            elif self.model.status == GRB.INFEASIBLE:
                print("Error: Model is infeasible.")
                # Compute and write IIS file to help debug
                print("Computing IIS (Irreducible Inconsistent Subsystem)...")
                self.model.computeIIS()
                self.model.write("one_price_model_infeasible.ilp")
                print("IIS written to one_price_model_infeasible.ilp")
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