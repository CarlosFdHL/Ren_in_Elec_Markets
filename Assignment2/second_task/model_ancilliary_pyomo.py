from pyomo.environ import ConcreteModel, Var, Param, Constraint, Objective, SolverFactory, NonNegativeReals, Binary, UnitInterval, maximize
import matplotlib.pyplot as plt
import numpy as np

# Plotting parameters
tt_params = {
    'font.family': 'serif',
    'font.size': 14
}
plt.rcParams.update(tt_params)

from .input_data import InputData

class AncilliaryServiceBiddingModelPyomo:
    def __init__(self, input_data: InputData, verbose: bool = True, solver: str = 'HiGHs'):
        if verbose:
            print('\n' + '-'*50)
            print(f"{'ANCILLIARY SERVICE BIDDING MODEL (Pyomo)':^50}")
            print('-'*50)
        self.data = input_data
        self.verbose = verbose
        self.model = ConcreteModel()
        self.solver = SolverFactory(solver)
        self._build_model()

    def build_variables(self):
        m = self.model
        m.bid_capacity = Var(self.data.H, domain=NonNegativeReals, name='bid_capacity')
        m.violation_binary = Var(
            [(h, m, w) for h in self.data.H for m in self.data.M for w in self.data.W],
            domain=Binary,
            name='violation_binary'
        )

    def build_constraints(self):
        m = self.model
        bigM = 1e9

        def capacity_limit_rule(model, h, m, w):
            return model.bid_capacity[h] - self.data.insample_scenarios[h*60 + m, w] <= bigM * model.violation_binary[h, m, w]

        m.capacity_limit = Constraint(
            [(h, m, w) for h in self.data.H for m in self.data.M for w in self.data.W],
            rule=capacity_limit_rule,
            name='capacity_limit'
        )

        def violation_limit_rule(model, h):
            return sum(
                model.violation_binary[h, m, w]
                for m in self.data.M for w in self.data.W
            ) <= self.data.max_violated_scenarios
        m.violation_limit = Constraint(self.data.H, rule=violation_limit_rule, name='violation_limit')

    def build_objective_function(self):
        m = self.model
        m.obj = Objective(
            expr=sum(m.bid_capacity[h] for h in self.data.H),
            sense=maximize,
            name='maximize_bid'
        )

    def _build_model(self):
        if self.verbose: print('\nBuilding model')
        self.build_variables()
        if self.verbose: print('Building constraints')
        self.build_constraints()
        if self.verbose: print('Building objective')
        self.build_objective_function()

    def run(self):
        result = self.solver.solve(self.model, tee=self.verbose)
        if self.verbose:
            print('Solver status:', result.solver.status)
        return self._extract_results()

    def run_hourly(self):
        bids = {}
        violations = {}
        violation_count = {}

        for h in self.data.H:
            if self.verbose:
                print(f"\nSolving for hour h = {h}")

            # Create a new model for each hour
            model = ConcreteModel()

            # Variables
            model.bid_capacity = Var(domain=NonNegativeReals, name=f'bid_capacity_{h}')
            model.violation_binary = Var(
                [(m, w) for m in self.data.M for w in self.data.W],
                domain=Binary,
                name=f'violation_binary_{h}'
            )

            # Parameters
            bigM = 1e9
                        # Constraints
            def capacity_limit_rule(model, m, w):
                minute_global = h * 60 + m
                return model.bid_capacity - self.data.insample_scenarios[minute_global, w] <= bigM * model.violation_binary[m, w]

            model.capacity_limit = Constraint(
                [(m, w) for m in self.data.M for w in self.data.W],
                rule=capacity_limit_rule,
                name=f'capacity_limit_{h}'
            )

            def violation_limit_rule(model):
                return sum(model.violation_binary[m, w] for m in self.data.M for w in self.data.W) <= self.data.max_violated_scenarios

            model.violation_limit = Constraint(rule=violation_limit_rule, name=f'violation_limit_{h}')

            # Objective
            model.obj = Objective(expr=model.bid_capacity, sense=maximize)

            # Solve
            result = self.solver.solve(model, tee=False)

            # Force the variables to be binary
            for m in self.data.M:
                for w in self.data.W:
                    model.violation_binary[m, w].value = round(model.violation_binary[m, w].value)
            
            if self.verbose:
                print('Solver status:', result.solver.status)
                # Print the selected capacity
                print(f"Selected capacity for hour {h}: {model.bid_capacity.value}")
                print(f"Violation count for hour {h}: {sum(model.violation_binary[m, w].value for m in self.data.M for w in self.data.W)}")

            # Extract results for this hour
            bids[h] = model.bid_capacity.value
            for m in self.data.M:
                for w in self.data.W:
                    violations[(h, m, w)] = model.violation_binary[m, w].value
            violation_count[h] = sum(
                model.violation_binary[m, w].value
                for m in self.data.M
                for w in self.data.W
            )

        return bids, violations, violation_count

    
    def _extract_results(self):
        m = self.model
        bids = {h: m.bid_capacity[h].value for h in self.data.H}
        violations = {
            (h, mmin, w): m.violation_binary[h, mmin, w].value
            for h in self.data.H
            for mmin in self.data.M
            for w in self.data.W
        }
        violation_count = {
            h: sum(
                violations[h, mmin, w]
                for mmin in self.data.M
                for w in self.data.W
            )
            for h in self.data.H
        }
        return bids, violations, violation_count

