import gurobipy as gp
from gurobipy import GRB
import pandas as pd

from input_data import InputData

class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass

class Step1_model:
    # Step1_model is a class that represents the optimization model. It receives an instance of the InputData class to build the optimization model and solve it.

    def __init__(self, input_data: InputData):
        # Initialize model attributes

        self.data = input_data
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
        self.build_model()

    def build_variables(self):
        # Create the variables

        for g in self.data.generators:
            for t in self.data.timeSpan:
                self.variables.production = {
                    (g, t): self.model.addVar(name=f"Production_{g}")
                    for g in self.data.generators
                    for t in self.data.timeSpan
                }
                    
    def build_constraints(self):
        # Create the constraints

        for g in self.data.generators:
            for t in self.data.timeSpan:
                if not self.data.wind[g]:
                    self.model.addLConstr(
                        self.variables.production[g, t],
                        GRB.LESS_EQUAL,
                        self.data.Pmax[g],
                        name = f"ProductionMAXLimit_{g}_{t}"
                    )
                else:
                    self.model.addLConstr(
                        self.variables.production[g, t], 
                        GRB.LESS_EQUAL, 
                        self.data.Pmax[g][t],
                        name = f"ProductionMAXLimit_{g}_{t}"
                    )
        
        self.constraints.production_lower_limit = {
            (g, t): self.model.addConstr(self.variables.production[g, t], 
                                         GRB.GREATER_EQUAL, 
                                         self.data.Pmin[g], 
                                         name=f"ProductionMINLimit_{g}")
            for g in self.data.generators
            for t in self.data.timeSpan
        }

        self.constraints.demand = {
            t: self.model.addConstr(gp.quicksum(self.variables.production[g, t] for g in self.data.generators), 
                                    GRB.EQUAL, 
                                    self.data.demand[t], 
                                    name=f"SystemDemandHour_{t}")
            for t in self.data.timeSpan
        } 
        
    def build_objective_function(self):
        # Create the objective function
        demand_cost = 0
        for t in self.data.timeSpan:
            demand_cost += gp.quicksum(self.data.demand_bid_price[t][i] * self.data.demand_per_load[i] 
                for i in range(len(self.data.demand_per_load)))
            
        producers_revenue = gp.quicksum(
            self.data.bid_offers[g] * self.variables.production[g, t] 
            for g in self.data.generators 
            for t in self.data.timeSpan
        )
        self.model.setObjective(demand_cost - producers_revenue, GRB.MAXIMIZE)

    def build_model(self):
        # Creates the model and calls the functions to build the variables, constraints, and objective function

        print("\nBuilding model")
        self.model = gp.Model(name="Investment Optimization Model")
        self.model.setParam('OutputFlag', 1)

        print("\nBuilding variables")
        self.build_variables()

        print("\nBuilding constraints")
        self.build_constraints()
        
        self.model.update()
        print(f"Number of variables: {self.model.NumVars}")
        print(f"Number of constraints: {self.model.NumConstrs}")

    def save_results(self):
        # Save the results in the results attribute

        print("\nSaving results")
        self.results.production = {
            (g, t): self.variables.production[g, t].x
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        self.results.objective = self.model.objVal
        self.results.price = {
            t: constraint.Pi for t, constraint in self.constraints.demand.items()
        }
        self.results.production_data = pd.DataFrame(index=self.data.timeSpan, columns=self.data.generators)
        self.results.profit_data = pd.DataFrame(index=self.data.timeSpan, columns=self.data.generators)

        for t, constraint in self.constraints.demand.items():
            for g in self.data.generators:
                self.results.production_data.at[t, g] = self.variables.production[g, t].X
                self.results.profit_data.at[t, g] = constraint.Pi * self.variables.production[g, t].X

    def print_results(self):
        # Print the results of the optimization problem

        print("\nPrinting results")
        
        print("\n1.-The market clearing price for each hour:")
        for t, price in self.results.price.items():
            print(f"Hour {t}: {price} $/MWh")

        print(f"\n2.-Social welfare of the system: {self.results.objective}")

        print("\nProduction for each generator")
        print(self.results.production_data)

        print("\n3.-Profit for each producer")
        print(self.results.profit_data)

        print("\n4.-Utility of each demand")
        

    def run(self):
        # Makes sure the model is solved and saves the results
        
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self.save_results()
        else:
            raise RuntimeError(f"\nOptimization of {self.model.ModelName} was not successful")



    
