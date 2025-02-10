import gurobipy as gp
from gurobipy import GRB
from step1.input_data import InputData

class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass

class step1_model:
    def __init__(self, input_data: InputData):
        self.data = input_data
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
        self.build_model()

    def build_variables(self):
        print("Building variables")
        for g in self.data.generators:
            for t in self.data.timeSpan:
                self.variables.production[g, t] = self.model.addVar(lb=self.data.Pmin[g], ub=self.data.Pmax[g], name=f"Production_{g}")
    def build_constraints(self):
        for g in self.data.generators:
            for t in self.data.timeSpan:
                self.constraints.production_limit[g, t] = self.model.addConstr(self.variables.production[g, t] <= self.data.Pmax[g], name=f"ProductionMAXLimit_{g}")
                self.constraints.production_limit[g, t] = self.model.addConstr(self.variables.production[g, t] >= self.data.Pmin[g], name=f"ProductionMINLimit_{g}")

        for t in self.data.timeSpan:
            for g in self.data.generators:
                self.data.demand[t] = self.model.addConstr(gp.quicksum(self.variables.production[g, t] for g in self.data.generators) == self.data.demand[t], name=f"SystemDemandHour_{t}")
        print("Optimizing model")
    
    
        
    def build_objective_function(self):
        for g in self.data.generators:
            for t in self.data.timeSpan:
                self.model.setObjective(self.data.bid_offers[g] * self.variables.production[g, t], GRB.MAXIMIZE)
        print("Building objective function")

    
    def save_results(self):
        print("Saving results")

    def build_model(self):
        self.build_variables()
        self.build_constraints()
        print("Building model")

    def print_results(self):
        print("Printing results")

    def run(self):
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()
        else:
            raise RuntimeError(f"Optimization of {self.model.ModelName} was not successful")



    
