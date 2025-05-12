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
    def __init__(self, input_data: InputData, verbose: bool = True, solver: str = 'pyomo'):
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
            [(h, mmin, w) for h in self.data.H for mmin in self.data.M for w in self.data.W],
            domain=Binary,
            name='violation_binary'
        )

    def build_constraints(self):
        m = self.model
        bigM = 1e18

        def capacity_limit_rule(model, h, mmin, w):
            return model.bid_capacity[h] <= (
                self.data.insample_scenarios[h*60 + mmin, w] + bigM * model.violation_binary[h, mmin, w]
            )
        m.capacity_limit = Constraint(
            [(h, mmin, w) for h in self.data.H for mmin in self.data.M for w in self.data.W],
            rule=capacity_limit_rule,
            name='capacity_limit'
        )

        def violation_limit_rule(model, h):
            return sum(
                model.violation_binary[h, mmin, w]
                for mmin in self.data.M for w in self.data.W
            ) <= self.data.epsilon_requirement * len(self.data.M) * len(self.data.W)
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

    def run_relaxed(self, delta: float = 1e-5):
        m = self.model
        # Relax binaries to continuous
        for h, mmin, w in m.violation_binary:
            m.violation_binary[h, mmin, w].domain = UnitInterval
        # ALSO-X style bisection
        q_low, q_high = 0, self.data.epsilon_requirement * len(self.data.M) * len(self.data.W)
        q = 0
        iteration = 0
        while q_high - q > delta:
            iteration += 1
            q = (q + q_high) / 2
            # update RHS of violation_limit
            for h in self.data.H:
                m.violation_limit[h].set_value(
                    sum(m.violation_binary[h, mmin, w] for mmin in self.data.M for w in self.data.W) <= q
                )
            self.solver.solve(m, tee=self.verbose)
            total_viol = sum(
                m.violation_binary[h, mmin, w].value
                for h in self.data.H for mmin in self.data.M for w in self.data.W
            )
            prob = total_viol / (len(self.data.H)*len(self.data.M)*len(self.data.W))
            if prob >= 1 - self.data.epsilon_requirement:
                q_high = q
            else:
                q_low = q
        return self._extract_results(), iteration, q, q_high
    
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

