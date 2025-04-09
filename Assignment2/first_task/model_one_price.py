import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt

# Plotting parameters: 
plt.rcParams['font.family'] = 'serif' 
plt.rcParams['font.size'] = 14

from .input_data import InputData

class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass

class OnePriceBiddingModel():
    
    def __init__(self, input_data: InputData):
        print()
        print('-' * 50)
        print(f'{"OFFERING STRATEGY BASED ON A ONE PRICE SCHEME":^30}')
        print('-' * 50)
        # Initialize model attributes
        self.data = input_data
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
        self.build_model()
    
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
        
    def build_objective_function(self):
        # Create the objective function

        # The objective function is defined as the profit from production and the profit from imbalance
        self.objective = self.data.prob_scenario * gp.quicksum(self.data.scenario[w]['eprice'][t] * self.variables.production[t] + # Profit from production
                                                          self.data.positiveBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w] * self.data.scenario[w]['sc'][t] +        # Profit from imbalance in case of system requiring upward balance
                                                          self.data.negativeBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w] * (1 - self.data.scenario[w]['sc'][t])    # Profit from imbalance in case of system requiring downward balance
                                                    for t in self.data.T
                                                    for w in self.data.W
                                                    ) 
        # The objective is to maximize profit
        self.model.setObjective(self.objective, GRB.MAXIMIZE)

    def build_model(self):
        # Creates the model and calls the functions to build the variables, constraints, and objective function

        print("\nBuilding model")
        self.model = gp.Model(name="OnePriceBiddingModel")
        self.model.setParam('OutputFlag', 0)

        print("\nBuilding variables")
        self.build_variables()

        print("\nBuilding constraints")
        self.build_constraints()
        
        print("\nBuilding objective function")
        self.build_objective_function()

        self.model.update()
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
        self.results.profit = self.model.ObjVal
        self.results.profit_production = {
            t: self.data.prob_scenario * gp.quicksum(self.data.scenario[w]['eprice'][t] * self.variables.production[t].X for w in self.data.W)
            for t in self.data.T
        }
        self.results.profit_imbalance = {
            t: self.data.prob_scenario * (
                gp.quicksum(self.data.positiveBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w].X * self.data.scenario[w]['sc'][t] for w in self.data.W) +
                gp.quicksum(self.data.negativeBalancePriceFactor * self.data.scenario[w]['eprice'][t] * self.variables.imbalance[t,w].X * (1 - self.data.scenario[w]['sc'][t]) for w in self.data.W)
            )
            for t in self.data.T
        }

        self.results.expected_real_prod = {
            t: self.data.prob_scenario * gp.quicksum(self.data.scenario[w]['rp'][t] for w in self.data.W) * self.data.p_nom
            for t in self.data.T
        }


    def print_results(self):
        print('-' * 30)
        print(f'{"Results Summary":^30}')
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
            profit_imbalance = self.results.profit_imbalance[t].getValue()  
            print(f'{t:^10} {profit_imbalance:^20.2f}')
        print('-' * 30)
        # Printing Total Profit
        print(f'Total Expected Profit: {self.results.profit:.2f} €')

    def plot(self):
        # Define figure 
        fig, ax = plt.subplots(figsize = (8,6))

        # Define arrays to be plotted
        profit_imbalance_values = [self.results.profit_imbalance[t].getValue() for t in self.data.T]
        profit_production_values = [self.results.profit_production[t].getValue() for t in self.data.T]
        total_profit = [profit_imbalance_values[i] + profit_production_values[i] for i, _ in enumerate(profit_production_values)]

        # Plot configuration
        ax.plot(self.data.T, profit_production_values, label='Profit from production', color='blue', marker = 'x', linestyle = '--')
        ax.plot(self.data.T, profit_imbalance_values, label='Expected profit from imbalance', color='red', marker = 'o', linestyle='-.')
        ax.plot(self.data.T, total_profit, color = 'black', label = 'Total profit')
        ax.set_ylabel('Profit (€)')
        ax.set_xlabel('Time (h)')
        ax.legend()
        ax.grid()
        plt.tight_layout()
        
            

    def run(self):
        # Makes sure the model is solved and saves the results
        try:
            self.model.optimize()
            self.model.write("model.lp")
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
                print("Optimization was successful!")
                self.save_results()     
            else:
                raise TimeoutError("Gurobi optimization failed")       
        except gp.GurobiError as e:
            print(f"Error reported: {e}")
            



    
