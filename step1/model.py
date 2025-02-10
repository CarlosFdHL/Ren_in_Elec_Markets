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
    
    def build_constraints(self):
        print("Optimizing model")
    
    
        
    def build_objective_function(self):
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



    
