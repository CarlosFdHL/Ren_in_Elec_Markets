import numpy as np
import pandas as pd
from sklearn.model_selection import ShuffleSplit
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB


from .input_data import InputData
from .model_one_price import OnePriceBiddingModel
from .model_two_price import TwoPriceBiddingModel


class RiskAverseExPostAnalysis:
    def __init__(self, input_data: InputData, beta=int, alpha=int, verbose: bool = True):
        self.data = input_data
        self.verbose = verbose
        self.model_type = self.data.model_type
        self.beta = beta
        self.alpha = alpha

        # Initialize containers for model components
        class ModelComponents: pass # Simple placeholder class
        self.variables = ModelComponents()
        self.constraints = ModelComponents()
        self.results = ModelComponents() # Also initialize results if you use it similarly
        
    def build_variables(self):
        # Create the variables

        # Bidded production
        self.variables.production = {
            t: self.model.addVar(lb = 0, name=f"Production_{t}")
            for t in self.data.T
        }

        # Imbalance of the generator
        self.variables.imbalance = {
            (t,w): self.model.addVar(lb=-self.data.p_nom, ub=self.data.p_nom, name=f"Imbalance_hour{t}_scenario{w}")
            for w in self.data.W
            for t in self.data.T
        }

        # Value at risk
        self.variables.value_at_risk = self.model.addVar(name=f"ValueAtRisk")

        # Auxiliary CVaR variable
        self.variables.auxiliary_cvar = {
            w: self.model.addVar(lb = 0, name=f"AuxiliaryCVaR_{w}")
            for w in self.data.W
        }

        if self.model_type == 'two_price':
            # Upward imbalance
            self.variables.up_imbalance = {
                (t,w): self.model.addVar(lb=0, name=f"UpImbalance_hour{t}_scenario{w}")
                for w in self.data.W
                for t in self.data.T
            }

            # Downward imbalance
            self.variables.down_imbalance = {
                (t,w): self.model.addVar(lb=0, name=f"DownImbalance_hour{t}_scenario{w}")
                for w in self.data.W
                for t in self.data.T
            }
    
    
    def build_constraints(self):
        # Create the constraints

        # PRODUCTION UPPER LIMIT
        # The production upper limit is defined as the maximum capacity of the generator
        self.constraints.production_upper_limit = {
            t: self.model.addConstr(self.variables.production[t],
                GRB.LESS_EQUAL,
                self.data.p_nom,
                name=f"ProductionUpperLimit_{t}"
            )
            for t in self.data.T
        }

        # IMABALANCE EQUALITY CONSTRAINT 
        # The imbalance is defined as the difference between the real production and the bidded production
        self.constraints.imbalance = {
            (t,w): self.model.addConstr(self.variables.imbalance[t,w],
                GRB.EQUAL,
                self.data.scenario[w]['rp'][t] * self.data.p_nom - self.variables.production[t],
                name=f"ImbalanceDefinition_{t}_{w}"
            )
            for t in self.data.T
            for w in self.data.W
        }

        # CVaR CONSTRAINTS
        if self.model_type == 'one_price':
            self.constraints.auxiliary_cvar = {
                w: self.model.addConstr(
                    self.variables.value_at_risk 
                    - self.data.prob_scenario * sum(                                                    # <-- Start profit calculation
                        self.data.scenario[w]['eprice'][t] * self.variables.production[t] +
                        self.data.positiveBalancePriceFactor * self.data.scenario[w]['eprice'][t] *
                            self.variables.imbalance[t, w] * self.data.scenario[w]['sc'][t] +
                        self.data.negativeBalancePriceFactor * self.data.scenario[w]['eprice'][t] *
                            self.variables.imbalance[t, w] * (1 - self.data.scenario[w]['sc'][t])      
                        for t in self.data.T
                    ),                                                                                  # <-- End profit calculation
                    GRB.LESS_EQUAL,
                    self.variables.auxiliary_cvar[w],

                    name=f"AuxiliaryCVaR_{w}"
                )
                for w in self.data.W
            }

        elif self.model_type == 'two_price':
            self.constraints.auxiliary_cvar = {
                w: self.model.addConstr(
                    self.variables.value_at_risk -
                    self.data.prob_scenario * sum(                                                                                              # <-- Start profit calculation
                        self.data.scenario[w]['eprice'][t] * self.variables.production[t]
                        + self.data.scenario[w]['sc'][t] * (
                            self.data.scenario[w]['eprice'][t] * self.variables.up_imbalance[t, w]
                            - self.data.positiveBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.down_imbalance[t, w]
                        )
                        + (1 - self.data.scenario[w]['sc'][t]) * (
                            self.data.negativeBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.up_imbalance[t, w]
                            - self.data.scenario[w]['eprice'][t] * self.variables.down_imbalance[t, w]
                        )
                        for t in self.data.T
                    ),                                                                                                                          # <-- End profit calculation
                    GRB.LESS_EQUAL,
                    self.variables.auxiliary_cvar[w],
                    name=f"AuxiliaryCVaR_{w}"
                )
                for w in self.data.W
            }

            # The imabalance is defined as the difference between the up and down imbalance
            self.constraints.imbalance_definition = {
                (t,w): self.model.addConstr(self.variables.imbalance[t,w],
                    GRB.EQUAL, 
                    self.variables.up_imbalance[t,w] - self.variables.down_imbalance[t,w],
                    name=f"ImbalanceDefinition_Hour{t}_Scenario{w}"
                )
                for t in self.data.T
                for w in self.data.W
            }
        
    def build_objective_function(self):
        # Create the objective function

        # The objective function is defined as the profit from production and the profit from imbalance plus the CVaR
        if self.model_type == 'one_price':
            self.objective_profit = self.data.prob_scenario * gp.quicksum(self.data.scenario[w]['eprice'][t] * self.variables.production[t] + # Profit from production
                                                            self.data.positiveBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w] * self.data.scenario[w]['sc'][t] +        # Profit from imbalance in case of system requiring upward balance
                                                            self.data.negativeBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w] * (1 - self.data.scenario[w]['sc'][t])    # Profit from imbalance in case of system requiring downward balance
                                                        for t in self.data.T
                                                        for w in self.data.W
                                                        ) 
        elif self.model_type == 'two_price':
            self.objective_profit = self.data.prob_scenario * gp.quicksum(self.data.scenario[w]['eprice'][t] * self.variables.production[t]                                                                     # Profit from production
                                                + self.data.scenario[w]['sc'][t] * (self.data.scenario[w]['eprice'][t] * self.variables.up_imbalance[t,w] 
                                                                                    - self.data.positiveBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.down_imbalance[t,w])           # Profit from imbalance in case of system requiring upward balance
                                                + (1 - self.data.scenario[w]['sc'][t]) * (self.data.negativeBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.up_imbalance[t,w] 
                                                                                    - self.data.scenario[w]['eprice'][t] * self.variables.down_imbalance[t,w])                                                  # Profit from imbalance in case of system requiring downward balance
                                            for t in self.data.T
                                            for w in self.data.W
                                            ) 
        self.objective_cvar = self.variables.value_at_risk - 1/(1-self.alpha) * sum(self.data.prob_scenario * self.variables.auxiliary_cvar[w] for w in self.data.W)
        # The objective is to maximize profit
        self.model.setObjective((1 - self.beta) * self.objective_profit + self.beta * self.objective_cvar , GRB.MAXIMIZE)

    def build_model(self):
        # Creates the model and calls the functions to build the variables, constraints, and objective function
        if self.verbose:
            print("\nBuilding model")
        
        self.model = gp.Model(name="OnePriceBiddingModel")
        self.model.setParam('OutputFlag', 1 if self.verbose else 0)
        
        if self.verbose:
            print("\nBuilding variables")
        self.build_variables()  

        if self.verbose:
            print("\nBuilding constraints")
        self.build_constraints()
        
        if self.verbose:
            print("\nBuilding objective function")
        self.build_objective_function()

        self.model.update()
        if self.verbose:
            print(f"Number of variables: {self.model.NumVars}")
            print(f"Number of constraints: {self.model.NumConstrs}")

    def save_results(self):
        # Saves the results of the model
        self.results.production = {
            t: self.variables.production[t].X
            for t in self.data.T
        }
        self.results.imbalance = {
            (t,w): self.variables.imbalance[t,w].X
            for t in self.data.T
            for w in self.data.W
        }
        self.results.expected_imbalance = {
            t: self.data.prob_scenario * sum(self.variables.imbalance[t, w].X for w in self.data.W)
            for t in self.data.T
        }
        self.results.profit_da = {
            t: self.data.prob_scenario * sum(self.data.scenario[w]['eprice'][t] * self.variables.production[t].X for w in self.data.W)
            for t in self.data.T
        }
        self.results.profit_imbalance = {
            (t,w): self.data.positiveBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w].X * self.data.scenario[w]['sc'][t]  +
                self.data.negativeBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w].X * (1 - self.data.scenario[w]['sc'][t])
                for t in self.data.T
                for w in self.data.W
        }
        self.results.expected_profit_imbalance = {
            t: self.data.prob_scenario * (
                sum(self.data.positiveBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w].X * self.data.scenario[w]['sc'][t] for w in self.data.W) +
                sum(self.data.negativeBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w].X * (1 - self.data.scenario[w]['sc'][t]) for w in self.data.W)
            )
            for t in self.data.T
        }

        self.results.expected_profit = {
            t: self.results.profit_da[t] + self.results.expected_profit_imbalance[t]
            for t in self.data.T
        }
        self.results.total_expected_profit = sum(self.results.expected_profit.values())

        self.results.profit_per_scenario = {
            w: gp.quicksum(self.data.scenario[w]['eprice'][t] * self.variables.production[t].X + self.results.profit_imbalance[t,w] for t in self.data.T)
            for w in self.data.W
        }

        self.results.expected_real_prod = {
            t: self.data.prob_scenario * gp.quicksum(self.data.scenario[w]['rp'][t] for w in self.data.W) * self.data.p_nom
            for t in self.data.T
        }

        total_production = sum(value for value in self.results.production.values())
        self.results.avg_bid = total_production / len(self.results.production)

        # Save CVaR results
        self.results.cvar = self.variables.value_at_risk.X - 1/(1-self.alpha) * sum(self.data.prob_scenario * self.variables.auxiliary_cvar[w].X for w in self.data.W)


    def print_results(self):
        print('-' * 30)
        print(f'{"Results Summary":^30}')
        print('-' * 30)
        
        print('-' * 30)
        print("Average bid: {:.2f} €".format(self.results.avg_bid))
        print('-' * 30)

        # Printing Production Results
        print(f'{"Production (MW)":^30}')
        print(f'{"Hour":^10} {"Production":^20}')
        print('-' * 30)
        for t in self.data.T:
            print(f'{t:^10} {self.results.production[t]:^20.2f}')
        print('-' * 30)

        # Printing Profit from Production
        print(f'{"Profit from Production (€)":^30}')
        print(f'{"Hour":^10} {"Profit (€)":^20}')
        print('-' * 30)
        for t in self.data.T:
            profit = self.data.scenario[1]['eprice'][t] * self.results.production[t]  # Assuming w=1 for simplicity
            print(f'{t:^10} {profit:^20.2f}')
        print('-' * 30)

        # Printing Profit from Imbalance
        print(f'{"Expected Profit from Imbalance (€)":^30}')
        print(f'{"Hour":^10} {"Profit (€)":^20}')
        print('-' * 30)
        for t in self.data.T:
            expected_profit_imbalance = self.results.expected_profit_imbalance[t]
            print(f'{t:^10} {expected_profit_imbalance:^20.2f}')
        print('-' * 30)
        # Printing Total Profit
        print(f'Total Expected Profit: {self.results.profit:.2f} €')

    def plot(self):
        # Define figure 
        fig, ax = plt.subplots(figsize = (8,6))

        # Define arrays to be plotted
        expected_profit_imbalance_values = [self.results.expected_profit_imbalance[t] for t in self.data.T]
        profit_da_values = [self.results.profit_da[t] for t in self.data.T]
        total_profit = [expected_profit_imbalance_values[i] + profit_da_values[i] for i, _ in enumerate(profit_da_values)]
        profit_per_scenario = [self.results.profit_per_scenario[w].getValue()for w in self.data.W]

        # Plot configuration
        ax.plot(self.data.T, profit_da_values, label='Profit from DA', color='blue', marker = 'x', linestyle = '--')
        ax.plot(self.data.T, expected_profit_imbalance_values, label='Expected profit from imbalance', color='red', marker = 'o', linestyle='-.')
        ax.plot(self.data.T, total_profit, color = 'black', label = 'Total profit')
        ax.set_ylabel('Profit (€)')
        ax.set_xlabel('Time (h)')
        ax.legend()
        ax.grid()


        # Plot cumulative profit distribution

        # Sort profit
        cumulative_profit = profit_per_scenario
        cumulative_profit.sort()

        # Acumulate profit
        cumulative_profit = np.cumsum(cumulative_profit)

        fig, ax = plt.subplots(1,2,figsize=(12, 6))

        ax[0].hist(profit_per_scenario, bins=30, alpha=0.75, color='blue', edgecolor='black')
        ax[0].set_title('Profit Distribution')
        ax[0].set_xlabel('Profit (€)')
        ax[0].set_ylabel('Scenarios')
        ax[0].grid()

        ax[1].step(range(len(cumulative_profit)), cumulative_profit, where='mid')
        ax[1].set_title('Cumulative Profit Distribution')
        ax[1].set_ylabel('Cumulative Profit (€)')
        ax[1].set_xlabel('Scenarios')
        ax[1].grid()
        plt.tight_layout()

        
            

    def run(self):
        # Makes sure the model is solved and saves the results
        try:
            self.model.optimize()
            self.model.write(f"{self.model_type}_model.lp")
            if self.model.status == gp.GRB.INFEASIBLE:
                print("Model is infeasible; computing IIS")
                self.model.computeIIS()
                self.model.write("model.ilp")  # Writes an ILP file with the irreducible inconsistent set.
                print("IIS written to model.ilp")
                exit()
            elif self.model.status == gp.GRB.UNBOUNDED:
                print("Model is unbounded")
                exit()
            elif self.model.status == gp.GRB.OPTIMAL:
                if self.verbose:
                    print("Optimization was successful!")
                self.save_results()     
            else:
                raise TimeoutError("Gurobi optimization failed")       
        except gp.GurobiError as e:
            print(f"Error reported: {e}")
            


