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

class Step3_zonal:
    # Step3_zonal1 is a class that represents the optimization model for zonal pricing. It receives an instance of the InputData class to build the optimization model and solve it.

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
            (d, t): self.model.addVar(lb = 0, name=f"Demand_{d}_{t}")
            for t in self.data.timeSpan
            for d in self.data.loads
        }
        
        # Create the flow variables
        self.variables.flow = {
            (a, b, t) : self.model.addVar(lb =-self.data.atc , ub =self.data.atc, name=f"flow_{a}_{b}_{t}")
            for t in self.data.timeSpan   
            for a in self.data.zones
            for b in self.data.zones if b != a  
        }
        
    def build_constraints(self):
        # Create the constraints for zonal limits 

        num_hours = len(self.data.timeSpan)
        num_days = num_hours // 24
        
        # Production upper limits limits. Makes distinction between wind and non-wind generators
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
        
        # Production lower limits
        self.constraints.production_lower_limit = {
            (g, t): self.model.addConstr(self.variables.production[g, t], 
                                         GRB.GREATER_EQUAL, 
                                         self.data.Pmin[g] ,
                                         name=f"ProductionMINLimit_{g}")
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        
        # Demand upper limit
        self.constraints.demand_upper_limit = {
            (d, t): self.model.addConstr(self.variables.demand[d, t],
                                        GRB.LESS_EQUAL,
                                        self.data.demand_per_load[d, n]/100 * self.data.demand[t-1],
                                        name=f"DemandUpperLimit_{d}_{t}")
            for t in self.data.timeSpan
            for (d, n) in self.data.demand_per_load.keys()
        }

        # Zonal balance constraint. Dual variable is the zonal price
        self.constraints.demand_equal_production = { 
            (a, t): self.model.addConstr(
                gp.quicksum(self.variables.demand[d, t] 
                    for (d, n) in self.data.demand_per_load.keys()  # Obtener nodo desde la demanda
                    if self.data.zone_mapping[n] == a) 
                + gp.quicksum(self.variables.flow[a, b, t] for b in self.data.zones if b != a)
                - gp.quicksum(self.variables.production[g, t] 
                    for g in self.data.generators 
                    if self.data.zone_mapping[self.data.P_node[g]] == a),
                GRB.EQUAL, 0, name=f"ZonalBalance_{a}_{t}"
            )
            for a in self.data.zones
            for t in self.data.timeSpan
        }

        # Flow limits between zones
        self.constraints.flow_limits = {
            (a, b, t): self.model.addConstr(
                self.variables.flow[a, b, t],
                GRB.EQUAL, -self.variables.flow[b , a, t],
                name=f"Flow_same_bus_{a}_{b}_{t}")
            for t in self.data.timeSpan
            for a in self.data.zones
            for b in self.data.zones if b != a
        }
        
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
        
        # Maximize the social welfare of the system
        self.model.setObjective(self.data.demand_cost - self.data.producers_cost, GRB.MAXIMIZE)

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

        print("\nSaving results")
        self.results.production = {
            (g, t): self.variables.production[g, t].x
            for g in self.data.generators
            for t in self.data.timeSpan
        }
        self.results.objective = self.model.objVal
        self.results.zonal_price = {
            (a, t): constraint.Pi for (a, t), constraint in self.constraints.demand_equal_production.items()
        }

        self.results.production_data = pd.DataFrame(index=self.data.timeSpan, columns=self.data.generators)
        self.results.profit_data = pd.DataFrame(index=self.data.timeSpan, columns=self.data.generators)
        self.results.utility = pd.DataFrame(index=self.data.timeSpan, columns=self.data.loads)
        
        self.results.sum_power = 0
        for (a, t), constraint in self.constraints.demand_equal_production.items():
            for g in self.data.generators:
                self.results.production_data.at[t, g] = self.variables.production[g, t].X
                self.results.sum_power += self.variables.production[g, t].X
                self.results.profit_data.at[t, g] = self.results.zonal_price[a, t] * self.variables.production[g, t].X
            
        for t_index, t in enumerate(self.data.timeSpan):
            for key in self.data.loads: 
                self.results.utility.at[t, key] = (self.data.demand_bid_price[t_index][key] - self.results.zonal_price[a, t]) * self.variables.demand[key, t].X
        
        self.results.flows = {
            (a, b, t): self.variables.flow[a, b, t].X
            for t in self.data.timeSpan
            for a in self.data.zones
            for b in self.data.zones if b != a
        }

        self.results.zone_generation = {
            (a, t): sum(
                self.variables.production[g, t].X
                for g in self.data.generators
                if self.data.zone_mapping[self.data.P_node[g]] == a
            )
            for a in self.data.zones
            for t in self.data.timeSpan
        }

        self.results.zone_demand = {
            (a, t): sum(
                self.variables.demand[d, t].X
                for (d, n) in self.data.demand_per_load.keys()
                if self.data.zone_mapping[n] == a
            )
            for a in self.data.zones
            for t in self.data.timeSpan
        }

    def print_results(self):
        # Print the results of the optimization problem
        
        print('-' * 70)  
        print(f'{"Printing results":^70}')
        print('-' * 70)  
        
        pd.set_option('display.max_columns', None)
        print("\nAvailable Transfer Capacity:", self.data.atc, "MW\n") 
    
        print('-' * 50)     
        #print("\n1.- Zonal prices")
        print(f'{"1.-Zonal prices":^50}')
        print('-' * 50)
        print(f'{"Hour":^5} {"Zone":^10} {"Price":^18}')
        for (a, t), price in self.results.zonal_price.items():
            print(f'{t:^5} {a:^10} {round(price, 3):^16} $/MWh')

        print(f"\n2.- Social Welfare of the System: {self.results.objective:.3f}\n")

        print('-' * 50)
        print(f'{"3.- Generation and Demand per Zone":^50}')
        print('-' * 50)
        print(f'{"Hour":^5} {"Zone":^10} {"Generation (MW)":^15} {"Demand (MW)":^18}')
        for t in self.data.timeSpan:
            for a in self.data.zones:
                generation = self.results.zone_generation[a, t]
                demand = self.results.zone_demand[a, t]
                print(f'{t:^5} {a:^10} {round(generation, 2):^15} {round(demand, 2):^18}')
        print("\n")       

        print('-' * 50)    
        print(f'{"4.-Flows between zones":^50}')
        print('-' * 50)   
        print(f'{"Hour":^5} {"From Zone":^10} {"To Zone":^15} {"Flow (MW)":^18}')
        for (a, b, t), flow in self.results.flows.items():
            print(f'{t:^5} {a:^10} {b:^15} {round(flow, 3):^18} MW')
        print('-' * 50)
        print("\n")   


        '''
        print('-' * 50)     
        print(f'{"5.- Production for Each Generator":^40}')
        print('-' * 50)
        print(f'{"Hour":^5} {"Generator":^15} {"Production (MW)":^18}')
        for (g, t), production in self.results.production.items():
            print(f'{t:^5} {g:^15} {round(production, 3):^18} MW')
        print('-' * 50)
        #print("Sum of all generations: ", self.results.sum_power, "MW")
        print("\n")

        print('-' * 50)     
        print(f'{"6.- Profit for Each Producer":^40}')
        print('-' * 50)
        print(f'{"Hour":^5} {"Generator":^15} {"Profit ($)":^18}')
        for (g, t), profit in self.results.profit_data.stack().items():
            print(f'{g:^5} {t:^15} {round(profit, 2):^18} $')
        print('-' * 50)
        print('-' * 50)     
        print(f'{"7.- Utility of Each Demand":^40}')
        print('-' * 50)
        print(f'{"Hour":^5} {"Load":^15} {"Utility ($)":^18}')
        for (t, key), utility in self.results.utility.stack().items():
            print(f'{t:^5} {key:^15} {round(utility, 2):^18} $')
        '''
        print('-' * 70)

        ###################################################
        
        #Plotting the zonal prices 
        
        zonal_price_dict = self.results.zonal_price  
        df_prices = pd.DataFrame(
            [(t, zone, price) for (zone, t), price in zonal_price_dict.items()],
             columns=["Time", "Zone", "Price"]
)
        df_plot = df_prices.pivot(index="Time", columns="Zone", values="Price")

        plt.figure(figsize=(10, 6))
        plt.plot(df_plot.index, df_plot["Zone A"], marker='o', color='blue', label='Zone A')
        plt.plot(df_plot.index, df_plot["Zone B"], marker='o', color='green', label='Zone B')
        #for zone in df_plot.columns:
        #    plt.plot(df_plot.index, df_plot[zone], marker='o', label=zone)

        plt.title("Market Clearing Price by Zone over Time")
        plt.xlabel("Hour")
        plt.ylabel("Price ($/MWh)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

        #######################################################
    def run(self):
        # Makes sure the model is solved and saves the results
        
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self.save_results()
        else:
            raise RuntimeError(f"\nOptimization of {self.model.ModelName} was not successful")



    
