import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import matplotlib.pyplot as plt

from input_data import InputData

'''
Although the model was built dependant on time, it was only meant to calculate for all the demand hours. 
This model does not include time dependant constraints like ramp up.
'''

class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass

class ReserveModel:
    # Reserve_model is a class that represents the optimization model. It receives an instance of the InputData class to build the optimization model and solve it.

    def __init__(self, input_data: InputData):
        # Initialize model attributes

        self.data = input_data
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
        self.build_model()

    def build_variables(self):
        # Create the variables

        self.variables.reserve_up = {
            (g, t): self.model.addVar(lb = 0, name=f"Reserve_up_{g}_{t}")
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        self.variables.reserve_down = {
            (g, t): self.model.addVar(lb = 0, name=f"Reserve_down_{g}_{t}")
            for g in self.data.generators
            for t in self.data.timeSpan
        }

    def build_constraints(self):
        # Create the constraints
        num_hours = len(self.data.timeSpan)
        num_days = num_hours // 24

        # Reserve up limit
        self.constraints.reserve_up_limit = {
            (g, t): self.model.addConstr(
                self.variables.reserve_up[g, t],
                GRB.LESS_EQUAL,
                self.data.Max_up_reserve[g] * self.data.offers_regulation[g],
                name = f"Reserve_up_limit_{g}_{t}"
            )
            for g in self.data.generators
            for t in self.data.timeSpan
        }

        # Reserve down limit
        self.constraints.reserve_down_limit = {
            (g, t): self.model.addConstr(
                self.variables.reserve_down[g, t],
                GRB.LESS_EQUAL,
                self.data.Max_down_reserve[g] * self.data.offers_regulation[g],
                name = f"Reserve_down_limit_{g}_{t}"
            )
            for g in self.data.generators
            for t in self.data.timeSpan
        }

        # Reserve up and down have to be less than the maximum capacity of the generator. Distinction between wind and non-wind generators
        self.constraints.reserve_limit = {}
        for g in self.data.generators:
            for t_index, t in enumerate(self.data.timeSpan):
                if self.data.wind[g]:
                    self.constraints.reserve_limit[g, t] = self.model.addConstr(
                        self.variables.reserve_up[g, t] + self.variables.reserve_down[g, t],
                        GRB.LESS_EQUAL,
                        self.data.Pmax[g][t_index - 24 * num_days],
                        name = f"Reserve_limit_{g}_{t}"
                    )
                else:
                    self.constraints.reserve_limit[g, t] = self.model.addConstr(
                        self.variables.reserve_up[g, t] + self.variables.reserve_down[g, t],
                        GRB.LESS_EQUAL,
                        self.data.Pmax[g],
                        name = f"Reserve_limit_{g}_{t}"
                    )

        # Reserve up has to be equal to the reserve up requirements of the system
        self.constraints.reserve_up_requirements = {
            t: self.model.addConstr(
                gp.quicksum(self.variables.reserve_up[g, t] for g in self.data.generators),
                GRB.EQUAL,
                self.data.upward_reserve_needed * self.data.demand[t-1],
                name = f"Reserve_up_requirements_{t}"
            )
            for t in self.data.timeSpan
        }
        
        # Reserve down has to be equal to the reserve down requirements of the system
        self.constraints.reserve_down_requirements = {
            t: self.model.addConstr(
                gp.quicksum(self.variables.reserve_down[g, t] for g in self.data.generators),
                GRB.EQUAL,
                self.data.downward_reserve_needed * self.data.demand[t-1],
                name = f"Reserve_down_requirements_{t}"
            )
            for t in self.data.timeSpan
        }
        
    def build_objective_function(self):
        # Create the objective function

        self.data.reserve_up_cost = gp.quicksum(self.variables.reserve_up[g, t] * self.data.bid_reserve_up[g] for g in self.data.generators for t in self.data.timeSpan)
        self.data.reserve_down_cost = gp.quicksum(self.variables.reserve_down[g, t] * self.data.bid_reserve_down[g] for g in self.data.generators for t in self.data.timeSpan)

        # Minimize the total reserve cost
        self.model.setObjective(self.data.reserve_up_cost + self.data.reserve_down_cost, GRB.MINIMIZE)

    def build_model(self):
        # Creates the model and calls the functions to build the variables, constraints, and objective function

        print("\nBuilding model")
        self.model = gp.Model(name="Investment Optimization Model")
        self.model.setParam('OutputFlag', 1)

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

        self.results.reserve_up = {
            (g, t): self.variables.reserve_up[g, t].x
            for g in self.data.generators 
            for t in self.data.timeSpan
        }
        self.results.reserve_down = {
            (g, t): self.variables.reserve_down[g, t].x
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        self.results.objective = self.model.objVal
        self.results.reserve_up_cost = {
            t: constraint.Pi for t, constraint in self.constraints.reserve_up_requirements.items()
        }
        self.results.reserve_down_cost = {
            t: constraint.Pi for t, constraint in self.constraints.reserve_down_requirements.items()
        }

        self.results.profit_reserve = pd.DataFrame(index=self.data.timeSpan, columns=self.data.generators)

        for t in self.data.timeSpan:
            for g in self.data.generators:
                self.results.profit_reserve.at[t, g] = self.results.reserve_up_cost[t] * self.results.reserve_up[g, t] +\
                      self.results.reserve_down_cost[t] * self.results.reserve_down[g, t]


    def print_results(self):
        # Print the results of the optimization problem
        print("\nPrinting results")

        print("\nObjective value: ", self.results.objective, "$")
        
        print("\nReserve up")
        for t in self.data.timeSpan:
            for g in self.data.generators:
                print(f"Hour {t}, Generator {g}: {self.results.reserve_up[g, t]}, MW")
        
        print("\nReserve down")
        for t in self.data.timeSpan:
            for g in self.data.generators:
                print(f"Hour {t}, Generator {g}: {self.results.reserve_down[g, t]}, MW")

        print("\nReserve up cost")
        for t in self.data.timeSpan:
            print(f"Hour {t}: {self.results.reserve_up_cost[t]}, $/MW")
        
        print("\nReserve down cost")
        for t in self.data.timeSpan:
            print(f"Hour {t}: {self.results.reserve_down_cost[t]}, $/MW")



    def run(self):
        # Makes sure the model is solved and saves the results
        
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self.save_results()
        else:
            raise RuntimeError(f"\nOptimization of {self.model.ModelName} was not successful")



    
