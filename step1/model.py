import gurobipy as gp
from gurobipy import GRB

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

    def print_results(self):
        print("\nPrinting results")
        for g in self.data.generators:
            for t in self.data.timeSpan:
                print(f"Production for Generator {g} at hour {t}: {self.results.production[g, t]} MW")

    def run(self):
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self.save_results()
        else:
            raise RuntimeError(f"\nOptimization of {self.model.ModelName} was not successful")



    
