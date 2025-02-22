import gurobipy as gp
from gurobipy import GRB
import pandas as pd

from input_data import InputData

class Expando(object):
    '''
        A small class which can have attributes set
    '''
    pass

class Step3_model:
    # Step3_model is a class that represents the optimization model. It receives an instance of the InputData class to build the optimization model and solve it.

    def __init__(self, input_data: InputData):
        # Initialize model attributes

        self.data = input_data
        self.zone_mapping = self.data.zone_mapping  # Define zone mapping 
        self.variables = Expando()
        self.constraints = Expando()
        self.results = Expando()
        self.build_model()

    def build_variables(self):
        # Create the variables

        self.variables.production = {
            (g, t): self.model.addVar(lb = 0, name=f"Production_{g}_{t}")
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        self.variables.demand = {
            (d, t): self.model.addVar(lb = 0, name=f"Demand_{t}")
            for t in self.data.timeSpan
            for d in self.data.loads
        }

        self.variables.angle = {
            (n) : self.model.addVar(lb = 0, ub = 360, name=f"Angle_{n}")
            for n in self.data.nodes
        }
        
    def build_constraints(self):
        # Create the constraints
        num_hours = len(self.data.timeSpan)
        num_days = num_hours // 24
        
        self.constraints.production_upper_limit = {}

        for g in self.data.generators:
            for t_index, t in enumerate(self.data.timeSpan):
                if not self.data.wind[g]:
                    constraint = self.model.addConstr(
                        self.variables.production[g, t], 
                        GRB.LESS_EQUAL,
                        self.data.Pmax[g],
                        name = f"ProductionMAXLimit_{g}_{t}"
                    )
                else:
                    constraint = self.model.addConstr(
                        self.variables.production[g, t], 
                        GRB.LESS_EQUAL, 
                        self.data.Pmax[g][t_index - 24 * num_days],
                        name = f"ProductionMAXLimit_{g}_{t}"
                    )
                self.constraints.production_upper_limit[g, t] = constraint
        
        self.constraints.production_lower_limit = {
            (g, t): self.model.addConstr(self.variables.production[g, t], 
                                         GRB.GREATER_EQUAL, 
                                         self.data.Pmin[g] ,
                                         name=f"ProductionMINLimit_{g}")
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        
        self.constraints.demand_upper_limit = {
            (d, t): self.model.addConstr(self.variables.demand[d, t],
                                        GRB.LESS_EQUAL,
                                        self.data.demand_per_load[d,n]/100 * self.data.demand[t-1],
                                        name=f"DemandUpperLimit_{t}")
            for t in self.data.timeSpan
            for (d, n) in self.data.demand_per_load.keys()
        }


        self.constraints.demand_equal_production_global = {
            t:  self.model.addConstr( - gp.quicksum(self.variables.production[g, t] for g in self.data.generators), 
                                    GRB.EQUAL, 
                                     - gp.quicksum(self.variables.demand[d, t] for d in self.data.loads), 
                                    name=f"SystemDemandEqualProductionHour_{t}")
            for t in self.data.timeSpan
        } 

        self.constraints.demand_equal_production = {
            (n, t): self.model.addConstr(
                -self.variables.demand[d, t] +
                -gp.quicksum(self.data.bus_reactance[n_, m] * (self.variables.angle[n_] - self.variables.angle[m])
                            for (n_, m) in self.data.bus_capacity.keys() if n_ == n) +  
                gp.quicksum(self.variables.production[g, t] for g in self.data.generators if self.data.P_node[g] == n),
                GRB.EQUAL, 0, name=f"BusBalance_{n}_{t}")
            for (d, n) in self.data.demand_per_load.keys()
            for t in self.data.timeSpan
        }

        self.constraints.max_bus_power = {
            (n, m, t): self.model.addConstr(
                1/ self.data.bus_reactance[n, m] * (self.variables.angle[n] - self.variables.angle[m]),
                GRB.LESS_EQUAL, self.data.bus_capacity[n, m],
                name=f"MaxBusPower_{n}_{m}_{t}"
            )
            for (n, m) in self.data.bus_reactance.keys()
            for t in self.data.timeSpan
        }

        self.constraints.min_bus_power = {
            (n, m, t): self.model.addConstr(
                1/ self.data.bus_reactance[n, m] * (self.variables.angle[n] - self.variables.angle[m]),
                GRB.GREATER_EQUAL, -self.data.bus_capacity[n, m],
                name=f"MaxBusPower_{n}_{m}_{t}"
            )
            for (n, m) in self.data.bus_reactance.keys()
            for t in self.data.timeSpan
        }

        self.model.addConstr(self.variables.angle[1], GRB.EQUAL, 0, name=f"Angle1")

        
    def build_objective_function(self):
        # Create the objective function

        self.data.demand_cost = 0
        for index, t in enumerate(self.data.timeSpan):
            self.data.demand_cost += gp.quicksum(self.data.demand_bid_price[index][d] * self.variables.demand[d, t]
                for d in self.data.loads
            )
        
        self.data.producers_cost = 0
        for t in self.data.timeSpan:
            self.data.producers_cost += gp.quicksum(self.data.bid_offers[g] * self.variables.production[g, t] for g in self.data.generators)
        
        self.model.setObjective(self.data.demand_cost - self.data.producers_cost, GRB.MAXIMIZE)
        #self.model.setObjective(producers_revenue, GRB.MINIMIZE)

    def build_model(self):
        # Creates the model and calls the functions to build the variables, constraints, and objective function

        print("\nBuilding model")
        self.model = gp.Model(name="Optimization Model")
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



    def compute_zonal_prices(self):
       
        # Compute zonal prices by averaging nodal prices within each zone
        zone_prices = {}

        for zone in set(self.zone_mapping.values()): 
            nodes_in_zone = [n for n, z in self.zone_mapping.items() if z == zone]
            nodal_prices = [self.results.price[n] for n in nodes_in_zone if n in self.results.price]

            # Compute the average price for the zone
            zone_prices[zone] = sum(nodal_prices) / len(nodal_prices) if nodal_prices else 0

        self.results.zonal_price = zone_prices


    def compute_atc(self):
        atc = {}
            
        # Sum up capacities of all lines connecting nodes from different zones
        for (from_node, to_node), capacity in self.data.bus_capacity.items():
            zone_from = self.zone_mapping[from_node]
            zone_to = self.zone_mapping[to_node]

            if zone_from != zone_to:
                atc_key = (zone_from, zone_to)
                atc[atc_key] = atc.get(atc_key, 0) + capacity

        self.results.atc = atc



    def save_results(self):
        # Save the results in the results attribute

        print("\nSaving results")
        self.results.production = {
            (g, t): self.variables.production[g, t].x
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        self.results.objective = self.model.objVal
        self.results.nodal_price = {
            (n, t): constraint.Pi for (n, t), constraint in self.constraints.demand_equal_production.items()
        }
        self.results.price = {
            t: constraint.Pi for t, constraint in self.constraints.demand_equal_production_global.items()
        }

        self.results.production_data = pd.DataFrame(index=self.data.timeSpan, columns=self.data.generators)
        self.results.profit_data = pd.DataFrame(index=self.data.timeSpan, columns=self.data.generators)
        self.results.utility = pd.DataFrame(index=self.data.timeSpan, columns=self.data.loads)

        self.results.sum_power = 0
        for (n, t), constraint in self.constraints.demand_equal_production.items():
            for g in self.data.generators:
                self.results.production_data.at[t, g] = self.variables.production[g, t].X
                self.results.sum_power += self.variables.production[g, t].X
                self.results.profit_data.at[t, g] = self.results.price[t] * self.variables.production[g, t].X
            
        for t_index, t in enumerate(self.data.timeSpan):
            for key in self.data.loads: 
                for n in self.data.nodes:
                    self.results.utility.at[t, key] = (self.data.demand_bid_price[t_index][key] - self.results.price[t]) * self.variables.demand[key, t].X

        # Compute zonal prices
        self.compute_zonal_prices()

        # Compute Available Transfer Capacities (ATC)
        self.compute_atc()
    

    def print_results(self):
        # Print the results of the optimization problem
        print("\nPrinting results")
        pd.set_option('display.max_columns', None)
        print("\n1.-The market clearing price for each hour:")
        for t, price in self.results.price.items():
            print(f"Hour {t}: {round(price, 3)} $/MWh")
        print("\nNodal prices")
        for (n, t), price in self.results.nodal_price.items():
            print(f"Hour {t}; Node {n}: {round(price, 3)} $/MWh")

        print(f"\n2.-Social welfare of the system: {self.results.objective}")

        print("\nProduction for each generator")
        print(self.results.production_data)
        print("Sum of all generations: ",self.results.sum_power, "MW")

        print("\n3.-Profit for each producer")
        print(self.results.profit_data)

        print("\n4.-Utility of each demand")
        
        print(self.results.utility)
        pd.reset_option('display.max_columns')

        print("\nZonal Market Prices:")
        for zone, price in self.results.zonal_price.items():
            print(f"{zone}: {price:.2f} $/MWh")

        print("\nAvailable Transfer Capacities (ATC) Between Zones:")
        for (zone_from, zone_to), capacity in self.results.atc.items():
            print(f"{zone_from} → {zone_to}: {capacity} MVA")
            

    def run(self):
        # Makes sure the model is solved and saves the results
        
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self.save_results()
        else:
            raise RuntimeError(f"\nOptimization of {self.model.ModelName} was not successful")



    
