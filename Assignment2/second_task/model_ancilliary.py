import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt
import numpy as np

# Plotting parameters: 
plt.rcParams['font.family'] = 'serif' 
plt.rcParams['font.size'] = 14

from .input_data import InputData

class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass

class AncilliaryServiceBiddingModel():
    
    def __init__(self, input_data: InputData, verbose: bool = True):
        if verbose:
            print()
            print('-' * 50)
            print(f'{"ANCILLIARY SERVICE BIDDING MODEL":^30}')
            print('-' * 50)
        # Initialize model attributes
        self.data = input_data
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
        self.verbose = verbose
        self.build_model()
    
    def build_variables(self):
        # Create the variables
        self.variables.bid_capacity = {
            h: self.model.addVar(vtype=GRB.CONTINUOUS, name=f"bid_capacity_Hour{h}", lb = 0)
            for h in self.data.H
        }
        
        self.variables.violation_binary = {
            (h, m, w): self.model.addVar(vtype=GRB.BINARY, name=f"violation_binary_{m}_{w}")
            for h in self.data.H
            for m in self.data.M
            for w in self.data.W
        }
        
    def build_constraints(self):
        # Create the constraints
        print(".")

        bigM = 1e6  # A large number to use as a big-M constant

        self.constraints.capacity_limit = {
            (h, m, w): self.model.addConstr(
                self.variables.bid_capacity[h] - self.data.insample_scenarios[h * 60 + m, w],
                GRB.LESS_EQUAL,
                bigM * self.variables.violation_binary[h, m, w], 
                name=f"capacity_limit_Hour{h}_Minute{m}_Scenario{w}"
            )
            for h in self.data.H
            for m in self.data.M
            for w in self.data.W
        }

        self.constraints.violation_limit = {
            h: self.model.addConstr(sum(self.variables.violation_binary[h, m, w] for m in self.data.M for w in self.data.W),
                GRB.LESS_EQUAL,
                self.data.max_violated_scenarios,
                name="violation_limit"
            )
        for h in self.data.H
        }
        
    def build_objective_function(self):
        # Create the objective function
        self.model.setObjective(gp.quicksum(self.variables.bid_capacity[h] for h in self.data.H), GRB.MAXIMIZE)


    def build_model(self):
        # Creates the model and calls the functions to build the variables, constraints, and objective function
        if self.verbose:
            print("\nBuilding model")
        
        self.model = gp.Model(name="OnePriceBiddingModel")
        self.model.setParam('OutputFlag', 0)
        
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
        self.results.bid_capacity = {
            h: self.variables.bid_capacity[h].X for h in self.data.H
        }
        self.results.violation_binary = {
            (h, m, w): self.variables.violation_binary[h, m, w].X
            for h in self.data.H
            for m in self.data.M
            for w in self.data.W
        }
        self.results.violation_count = {
            h: sum(self.results.violation_binary[h, m, w] for m in self.data.M for w in self.data.W)
            for h in self.data.H
        }

    def print_results(self):
        
        print("Capacity Bidded each Hour:")
        for h in self.data.H:
            print(f"Hour {h}: {self.results.bid_capacity[h]}")
        print("\nNumber of Violations each Hour:")
        for h in self.data.H:
            print(f"Hour {h}: {self.results.violation_count[h]}")
        
        
    def run(self):
        # Makes sure the model is solved and saves the results
        try:
            self.model.optimize()
            self.model.write("first_task/p90_model.lp")
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
            



    
