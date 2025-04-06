import gurobipy as gp
from gurobipy import GRB

from .input_data import InputData

class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass

class OnePriceBiddingModel():
    
    def __init__(self, input_data: InputData):
        # Initialize model attributes
        self.model = gp.Model("OnePriceBiddingModel")
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
    
    def build_variables(self):
        # Create the variables
        power_bid_da = {
            (g, t): self.model.addVar(lb = 0, name=f"PowerBidDA_{g}_{t}")
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        print("*")
        
    def build_constraints(self):
        # Create the constraints
        print("*")
        
    def build_objective_function(self):
        # Create the objective function
        print("*")
        
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
        # Saves the results of the model
        print("*")

    def print_results(self):
        print("*")
            

    def run(self):
        # Makes sure the model is solved and saves the results
        
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self.save_results()
        else:
            raise RuntimeError(f"\nOptimization of {self.model.ModelName} was not successful")



    
