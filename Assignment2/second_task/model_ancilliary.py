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
        bigM = 1e3  # A large number to use as a big-M constant

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
        
        self.model = gp.Model(name="AncilliaryServiceBiddingModel")
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
    
    def verify_p90_out_of_sample(self):
        """
        Verifies the P90 requirement using out-of-sample testing profiles.

        Args:
            outsample_scenarios: containing the out-of-sample scenarios.

        """
        num_hours = len(self.data.H)
        num_minutes = len(self.data.M)
        num_profiles = self.data.n_outsample_scenarios
        p90_threshold = self.data.epsilon_requirement  # Defined in input_data.py

        print("\n--- P90 Out-of-Sample Verification ---")
        for h in self.data.H:
            bid = self.results.bid_capacity[h]
            # Count violations for each profile
            violations_per_profile = []
            for w in self.data.W_outsample:
                violations = 0
                for m in self.data.M:
                    minute_idx = h * num_minutes + m
                    if bid > self.data.outsample_scenarios[minute_idx, w]:
                        violations += 1
                violations_per_profile.append(violations)
            # Calculate the fraction of minutes where bid was not enough (per profile)
            violation_fractions = [v / num_minutes for v in violations_per_profile]
            # P90 requirement: at least 90% of minutes per profile should be covered
            satisfied_profiles = [frac <= p90_threshold for frac in violation_fractions]
            p90_satisfied = sum(satisfied_profiles) / num_profiles >= 0.9

            print(f"Hour {h}:")
            print(f"  Profiles satisfying P90: {sum(satisfied_profiles)}/{num_profiles}")
            print(f"  P90 requirement satisfied: {p90_satisfied}")
    
    def run_relaxed(self, delta=1e-2):
        """
        Solves the model using the ALSO-X algorithm by iteratively relaxing the binary constraints.

        Args:
            delta (float): Stopping tolerance parameter.
            epsilon (float): Maximum violation probability threshold.
        """
        # Step 1: Initialize q and q_bar
        q_low = [0 for _ in self.data.H]

        q_up = [
            self.data.epsilon_requirement * len(self.data.W) ** 2
            for _ in self.data.H
        ]
        q_low = np.array(q_low)
        q_up = np.array(q_up)
        
        # Initialize q as a zero vector to store the midpoint values for each hour
        q = np.zeros(len(self.data.H))

        # Relax the integrality of the binary variables
        for (h, m, w), var in self.variables.violation_binary.items():
            var.vtype = GRB.CONTINUOUS
            var.lb = 0
            var.ub = 1

        self.model.update()
        it = 0
        # Step 2: Iterative process

        while np.all(q_up - q_low >= delta):
            it += 1
            # Step 3: Set q as the midpoint and update the violation limit constraint
            for h in self.data.H:
                q[h] = (q_low[h] + q_up[h]) / 2
                self.constraints.violation_limit[h].RHS = q[h]                

            self.model.update()

            # Step 4: Solve the relaxed problem
            self.model.optimize()

            if self.model.status != GRB.OPTIMAL:
                raise RuntimeError("Optimization failed during ALSO-X execution.")

            # Step 5: Check the probability condition
            violation_prob = np.zeros(len(self.data.H))
            for h in self.data.H:
                violation_prob[h] = sum(
                    1 - self.variables.violation_binary[h, m, w].X
                    for m in self.data.M
                    for w in self.data.W
                ) / (len(self.data.M) * len(self.data.W))

                if violation_prob[h] >= 1 - self.data.epsilon_requirement:
                    q_low[h] = q[h]
                else:
                    q_up[h] = q[h]
        self.model.write("second_task/output/verification/ancilliary_model.lp")
        self.save_results() 
        # print(self.variables.violation_binary[0,0,5].X)
        print(f"\nSolved in {it} iterations") 
        print(f"Final q: {q}")

    def run_hourly(self):
        """
        Solves the model independently for each hour.
        """
        bids = {}
        violations = {}
        violation_count = {}

        for h in self.data.H:
            if self.verbose:
                print(f"\nSolving for hour h = {h+1}")

            # Create a new model for each hour
            model = gp.Model(name=f"AncilliaryServiceBiddingModel_Hour{h}")
            model.setParam('OutputFlag', 0)

            # Variables
            bid_capacity = model.addVar(vtype=GRB.CONTINUOUS, name=f"bid_capacity_Hour{h}", lb=0)
            violation_binary = {
                (m, w): model.addVar(vtype=GRB.BINARY, name=f"violation_binary_{m}_{w}")
                for m in self.data.M
                for w in self.data.W
            }

            # Constraints
            bigM = 1e3  # A large number to use as a big-M constant

            # Capacity limit constraints
            capacity_limit = {
                (m, w): model.addConstr(
                    bid_capacity - self.data.insample_scenarios[h * 60 + m, w],
                    GRB.LESS_EQUAL,
                    bigM * violation_binary[m, w],
                    name=f"capacity_limit_Hour{h}_Minute{m}_Scenario{w}"
                )
                for m in self.data.M
                for w in self.data.W
            }

            # Violation limit constraint
            violation_limit = model.addConstr(
                gp.quicksum(violation_binary[m, w] for m in self.data.M for w in self.data.W),
                GRB.LESS_EQUAL,
                self.data.max_violated_scenarios,
                name=f"violation_limit_Hour{h}"
            )

            # Objective function
            model.setObjective(bid_capacity, GRB.MAXIMIZE)

            # Solve the model
            model.optimize()

            if model.status == GRB.OPTIMAL:
                if self.verbose:
                    print(f"Optimization successful for hour {h}")
                    print(f"Selected capacity for hour {h}: {bid_capacity.X}")
                    print(f"Violation count for hour {h}: {sum(violation_binary[m, w].X for m in self.data.M for w in self.data.W)}")

                # Store results
                bids[h] = bid_capacity.X
                for m in self.data.M:
                    for w in self.data.W:
                        violations[(h, m, w)] = violation_binary[m, w].X
                violation_count[h] = sum(
                    violation_binary[m, w].X for m in self.data.M for w in self.data.W
                )
            else:
                print(f"Optimization failed for hour {h} with status {model.status}")

        # Save results
        self.results.bid_capacity = bids
        self.results.violation_binary = violations
        self.results.violation_count = violation_count

        # if self.verbose:
            # self.print_results()
    def run(self):
        # Makes sure the model is solved and saves the results
        try:
            self.model.optimize()
            self.model.write("second_task/output/verification/ancilliary_model.lp")
            if self.model.status == gp.GRB.INFEASIBLE:
                print("Model is infeasible; computing IIS")
                self.model.computeIIS()
                self.model.write("second_task/output/verification/ancilliary_model.ilp")  # Writes an ILP file with the irreducible inconsistent set.
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
            



    
