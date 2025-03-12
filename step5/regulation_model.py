import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import matplotlib.pyplot as plt

from input_data_day_ahead import InputDataDayAhead
from input_data_regulation import InputDataRegulation

class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass

class RegulationModel:
    # RegulationModel is a class that represents the regulation market after the day ahead market. It receives an instance of the InputData class to build the optimization model and solve it.

    def __init__(self, input_data_da: object, input_data_regulation: InputDataRegulation):
        # Initialize model attributes

        self.data_da = input_data_da
        self.data_regulation = input_data_regulation
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
        self.build_model()

    def build_variables(self):
        # Create the variables
        self.variables.upward_regulation = {
            (g, t): self.model.addVar(lb = 0, name=f"UpwardRegulation_{g}_{t}")
            for g in self.data_da.data.generators
            for t in self.data_da.data.timeSpan
        }
        self.variables.downward_regulation = {
            (g, t): self.model.addVar(lb = 0, name=f"DownwardRegulation_{g}_{t}")
            for g in self.data_da.data.generators
            for t in self.data_da.data.timeSpan
        }
        self.variables.demand_curtailment = {
            (d, t): self.model.addVar(lb = 0, name=f"DemandCurtailment_{d}_{t}")
            for t in self.data_da.data.timeSpan
            for d in self.data_da.data.loads
        }
          
    def build_constraints(self):
        # Create the constraints

        self.constraints.upward_regulation_max = {
            (g, t): self.model.addConstr(
                self.variables.upward_regulation[g, t],
                GRB.LESS_EQUAL,
                self.data_regulation.up_regulation_max[g, t],
                name=f"UpwardRegulationMax_{g}_{t}"
            )
            for g in self.data_da.data.generators if self.data_da.data.wind[g] == False
            for t in self.data_da.data.timeSpan
        }

        self.constraints.downward_regulation_max = {
            (g, t): self.model.addConstr(
                self.variables.downward_regulation[g, t],
                GRB.LESS_EQUAL,
                self.data_regulation.up_regulation_max[g, t],
                name=f"DownwardRegulationMax_{g}_{t}"
            )
            for g in self.data_da.data.generators if self.data_da.data.wind[g] == False
            for t in self.data_da.data.timeSpan
        }

        self.data_regulation.balance ={
            t: gp.quicksum(self.data_regulation.variation[g,t] for g in self.data_da.data.generators)
            for t in self.data_da.data.timeSpan
        }

        self.constraints.sum_equal_balance = {
            t: self.model.addConstr(
                gp.quicksum(self.variables.upward_regulation[g, t] for g in self.data_da.data.generators) 
                - gp.quicksum(self.variables.downward_regulation[g, t] for g in self.data_da.data.generators),
                GRB.EQUAL,
                self.data_regulation.balance[t],
                name=f"SumEqualBalance_{t}"
            )
            for t in self.data_da.data.timeSpan
        }
        
    def build_objective_function(self):
        # Create the objective function

        self.data_regulation.upward_cost = gp.quicksum(self.variables.upward_regulation[g, t]
                                            for g in self.data_da.data.generators for t in self.data_da.data.timeSpan) 
        self.data_regulation.downward_cost = gp.quicksum(self.variables.downward_regulation[g, t]
                                              for g in self.data_da.data.generators for t in self.data_da.data.timeSpan) 
        self.data_regulation.curtailment_cost = gp.quicksum(self.data_da.data.curtailment_cost * self.variables.demand_curtailment[d, t]
                                                for d in self.data_da.data.loads for t in self.data_da.data.timeSpan)
        
        self.model.setObjective(self.data_regulation.upward_cost - self.data_regulation.downward_cost, GRB.MINIMIZE)

    def build_model(self):
        # Creates the model and calls the functions to build the variables, constraints, and objective function

        print("\nBuilding model")
        self.model = gp.Model(name="Optimization Model")
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
        # Save the results in the results attribute

        print("\nSaving results")

        self.results.objective = self.model.objVal

        self.results.balance_price = {
            t: constraint.Pi for t, constraint in self.constraints.sum_equal_balance.items()
        }
        
        self.results.demand_curtailment = pd.DataFrame(index=self.data_da.data.timeSpan, columns=self.data_da.data.loads)

        for t in self.data_da.data.timeSpan:
            for d in self.data_da.data.loads:
                self.results.demand_curtailment.at[t, d] = self.variables.demand_curtailment[d, t].X
        
        self.results.profit_data = self.data_da.results.profit_data
        self.results.regulation_profit = pd.DataFrame(index=self.data_da.data.timeSpan, columns=self.data_da.data.generators)
        if self.data_da.data.regulation_pricing.lower() == 'one price':
            for t in self.data_da.data.timeSpan:
                for g in self.data_da.data.generators:
                    self.results.regulation_profit.at[t, g] = self.variables.upward_regulation[g, t].X * self.results.balance_price[t] -\
                                                            self.variables.downward_regulation[g, t].X * self.results.balance_price[t]      
                    self.results.profit_data.at[t, g] += self.results.regulation_profit.at[t, g]
        elif self.data_da.data.regulation_pricing.lower() == 'two price':
            for t in self.data_da.data.timeSpan:
                for g in self.data_da.data.generators:
                    self.results.regulation_profit.at[t, g] = self.variables.upward_regulation[g, t].X * self.data_da.results.price[t] -\
                                                            self.variables.downward_regulation[g, t].X * self.data_da.results.price[t]
                    self.results.profit_data.at[t, g] += self.results.regulation_profit.at[t, g]

        else: 
            print("Invalid regulation pricing")
            raise ValueError

        for t in self.data_da.data.timeSpan:
            for g in self.data_da.data.generators:
                self.results.demand_curtailment.at[t, g] = self.variables.demand_curtailment[g, t].X

    def print_results(self):
        # Print the results of the optimization problem
        print("\nPrinting results")
        
        print(f"Objective function value: {self.results.objective}")

        print("\nBalance price")
        pd.set_option('display.max_columns', None)
        print(self.results.balance_price)
        pd.reset_option('display.max_columns')

        print("\nDemand curtailment")
        print(self.results.demand_curtailment)

        print("\nProfit for each producer")
        print(self.results.profit_data)

        print("\nRegulation profit for each generator")
        print(self.results.regulation_profit)

    def plotting_results(self):
    # Plotting the results of the optimization problem

        for t, price in self.results.price.items():
            plt.plot(t, price)
            plt.xlabel("Hour")
            plt.ylabel("Price $/MWh")
            plt.title("Market clearing price for each hour")
            plt.show()

    def run(self):
        # Makes sure the model is solved and saves the results
        
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self.save_results()
        else:
            raise RuntimeError(f"\nOptimization of {self.model.ModelName} was not successful")



    
