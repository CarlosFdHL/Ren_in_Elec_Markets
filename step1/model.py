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
    def __init__(self, input_data: InputData):
        self.data = input_data
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
        self.build_model()

    def build_variables(self):
        for g in self.data.generators:
            for t in self.data.timeSpan:
                self.variables.production = {
                    (g, t): self.model.addVar(lb=self.data.Pmin[g], ub=self.data.Pmax[g], name=f"Production_{g}")
                    for g in self.data.generators
                    for t in self.data.timeSpan
                }
                    
    def build_constraints(self):
        self.constraints.production_upper_limit = {
            (g, t): self.model.addConstr(self.variables.production[g, t], 
                                         GRB.LESS_EQUAL, 
                                         self.data.Pmax[g], 
                                         name=f"ProductionMAXLimit_{g}")
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        
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
        demand_cost = gp.quicksum(
            self.data.demand_bid_price * self.data.demand[t] 
            for t in self.data.timeSpan
        )
        producers_revenue = gp.quicksum(
            self.data.bid_offers[g] * self.variables.production[g, t] 
            for g in self.data.generators 
            for t in self.data.timeSpan
        )
        self.model.setObjective(demand_cost - producers_revenue, GRB.MAXIMIZE)

    def build_model(self):
        print("\nBuilding model")
        self.model = gp.Model(name="Investment Optimization Model")
        self.model.setParam('OutputFlag', 1)

        print("\nBuilding variables")
        self.build_variables()

        print("\nBuilding constraints")
        self.build_constraints()
        
        print(f"Number of variables: {self.model.NumVars}")
        print(f"Number of constraints: {self.model.NumConstrs}")
        self.model.update()

    def save_results(self):
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
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self.save_results()
        else:
            raise RuntimeError(f"\nOptimization of {self.model.ModelName} was not successful")



    
