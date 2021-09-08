"""
Simplified Modell for internal use.
"""

import os
from warnings import warn
import pyomo.environ as pyo
import pandas as pd
import numpy as np


class Project(object):
    def __init__(self, name, typ):
        self.name = name
        self.typ = typ

        # todo: add the weather information (temperature and irradiance) and
        #  price information (energy price, emission)
        self.environment = None

        self.district_list = []
        self.building_list = []

        self.model = None

    def add_environment(self, environment):
        """
        Add the environment object, which contains the weather and price
        information, into the project.
        Args:
            environment:
        """
        if self.environment is not None:
            warn('There is already an environment object in the project!')
        else:
            self.environment = environment

    def add_building(self, building):
        """
        Add a building to the Project object.
        Args:
            building: the Building object, which is defined by Building.py
        """
        self.building_list.append(building)

    def add_district(self, district):
        """
        Add district object to the project
        Args:
            district:
        """
        pass

    def build_model(self):
        """
        Build up a mathematical model (concrete model) using pyomo modeling
        language for optimization.
        """
        if self.typ == 'building' and len(self.building_list) == 1:
            # Initialisation of ConcreteModel
            self.model = pyo.ConcreteModel(self.name)
            self.model.cons = pyo.ConstraintList()

            # Define pyomo variables
            bld = self.building_list[0]
            # print(bld.topology)
            # Add flow dependent decision variables
            # for var in self.__var_dict:
            #     # Till here, var_dict only contains power flow variables, thus all time related
            #     for t in self.__time_steps:
            #         self.__var_dict[var][t] = pyo.Var(bounds=(0, None))
            #         self.__model.add_component(var[0] + '_' + var[1] + "_%s" % t,
            #                                    self.__var_dict[var][t])
            #
            # # Add component dependent decision variables
            # for comp in self.__components:
            #     self.__components[comp].add_variables(self.__input_profiles,
            #                                           self.__plant_parameters,
            #                                           self.__var_dict,
            #                                           self.__flows, self.__model,
            #                                           self.__time_steps)
            #
            # # Add component dependent constraints
            # for comp in self.__components:
            #     self.__components[comp].add_all_constr(self.__model, self.__flows,
            #                                            self.__var_dict,
            #                                            self.__time_steps)
            #
            # # Instantiate EMS component and implement the strategies
            # if set(strategy_name).issubset(self.__strategy_list):
            #     ems = components_list['EnergyManagementSystem'](self.__name, self.__configuration, strategy_name,
            #                                                     self.__plant_parameters, self.__flows, self.__components,
            #                                                     self.__component_properties)
            #     ems.implement_strategy(self.__model, self.__var_dict, self.__time_steps)
            # else:
            #     print('Not all strategies are defined for this prosumer. Use add_strategy to complete the strategy list.')
        else:
            pass

    def run_optimization(self, strategy_name, solver_name='gurobi', commentary=False, pareto_set_size=5):
        self.__build_math_model(strategy_name, components)
        solver = pyo.SolverFactory(solver_name)
        # solver.options['Heuristics'] = 0.05
        # solver.options['MIPGap'] = 0.01
        # solver.options['ImproveStartGap'] = 0.04
        # solver.options['MIPFocus'] = 3  # 1
        # solver.options['Presolve'] = 2  # this can be helpful!
        # solver.options['NumericFocus'] = 1
        # glpk(bad for milp), cbc(good for milp), gurobi: linear, ipopt: nonlinear
        # in order to install a new solver paste the .exe file in env. path 'C:\Users\User\anaconda3\envs\envINEED'
        if len(strategy_name) == 1:
            # solver.options['NonConvex'] = 2  # only for gurobi nlp
            self.__solver_result = solver.solve(self.__model, tee=commentary)
            if (self.__solver_result.solver.status == SolverStatus.ok) and (
                    self.__solver_result.solver.termination_condition == TerminationCondition.optimal):
                self.__rsl = {0: self.__extract_results()}
            else:
                print('ERROR: The model is infeasible or unbounded: no optimal solution found')
        elif len(strategy_name) > 1:
            # using Augmented Epsilon Constraint as presented in Mavrotas 2009: Effective implmentation of the e-constraint
            # method in Multi-Objective Mathematical Programming problems

            self.__model.O_f2.deactivate()  # deactivates second objective function

            # solve for first iteration of max f1
            solver.solve(self.__model, tee=commentary)

            print('Non pareto optimal solution of max f1')
            # print('( X1 , X2 ) = ( ' + str(pyo.value(model.X1)) + ' , ' + str(pyo.value(model.X2)) + ' )')
            print('f1 = ' + str(pyo.value(self.__model.f1)))
            print('f2 = ' + str(pyo.value(self.__model.f2)))

            f1_max = pyo.value(self.__model.f1)

            # max f2
            self.__model.O_f2.activate()  # activate the second objective function
            self.__model.O_f1.deactivate()  # deactivate the first objective function

            ## restrict the first objective to be its maximum and solve the second
            self.__model.C4 = pyo.Constraint(expr=self.__model.f1 == f1_max)

            solver.solve(self.__model, tee=commentary)

            payoff_table = {'f1': [], 'f2': []}

            print('Pareto optimal (lexicographic) solution of max f1: payoff table')
            # print('( X1 , X2 ) = ( ' + str(value(model.X1)) + ' , ' + str(value(model.X2)) + ' )')
            print('f1 = ' + str(pyo.value(self.__model.f1)))
            payoff_table['f1'].append(pyo.value(self.__model.f1))
            print('f2 = ' + str(pyo.value(self.__model.f2)))
            payoff_table['f2'].append(pyo.value(self.__model.f2))
            f2_min = pyo.value(self.__model.f2)

            ## cancel the restriction and resolve the second objective function
            self.__model.C4.deactivate()

            solver.solve(self.__model, tee=commentary)

            print('Optimal solution of max f2 (not necessary pareto optimal but irrelevant since we only need the values of f2 for '
                'pareto set: payoff table')
            # print('( X1 , X2 ) = ( ' + str(value(model.X1)) + ' , ' + str(value(model.X2)) + ' )')
            print('f1 = ' + str(pyo.value(self.__model.f1)))
            payoff_table['f1'].append(pyo.value(self.__model.f1))
            print('f2 = ' + str(pyo.value(self.__model.f2)))
            payoff_table['f2'].append(pyo.value(self.__model.f2))

            self.__payoff = pd.DataFrame(payoff_table, index=['maxf1', 'maxf2'])

            f2_max = pyo.value(self.__model.f2)

            if f2_min > f2_max:
                f2_max = f2_min

            # apply augmented $\epsilon$-Constraint

            print('f2_min and f2_max are the bounds of epsilon2: [' + str(
                    f2_min) + ', ' + str(f2_max) + ']' +
                  ' Each iteration will keep f2 between f2_min and f2_max.')

            steps = list(np.linspace(f2_min, f2_max, pareto_set_size))

            print('Size of pareto set is:', len(steps))
            print('Range of f2 is:', steps)

            # max   f2 + delta*epsilon
            #  s.t. f2 - s = e

            self.__model.del_component(self.__model.O_f1)
            self.__model.del_component(self.__model.O_f2)

            self.__model.e = pyo.Param(initialize=0, mutable=True)

            self.__model.eps = pyo.Param(initialize=0.00001)

            r2 = f2_max - f2_min
            if r2 == 0:
                r2 = 1

            self.__model.r2 = pyo.Param(initialize=r2)

            # Define slack variable for f2
            self.__model.s2 = pyo.Var(bounds=(0, None))

            self.__model.O_f1 = pyo.Objective(
                expr=self.__model.f1 + self.__model.eps * self.__model.s2 / self.__model.r2,
                sense=pyo.maximize)

            self.__model.C_e = pyo.Constraint(
                expr=self.__model.f2 - self.__model.s2 == self.__model.e)

            f1_l = []
            f2_l = []
            pareto_set_rsl = dict()
            j = 0

            for i in tqdm(steps):
                self.__model.e = i
                self.__solver_result = solver.solve(self.__model,
                                                    tee=commentary)
                if (self.__solver_result.solver.status == SolverStatus.ok) and (
                        self.__solver_result.solver.termination_condition == TerminationCondition.optimal):
                    f1_l.append(pyo.value(self.__model.f1))
                    f2_l.append(pyo.value(self.__model.f2))
                    pareto_set_rsl[j] = self.__extract_results()
                    j += 1
                else:
                    print(
                        'ERROR: The model is infeasible or unbounded: no optimal solution found')

            self.__rsl = pareto_set_rsl
            self.__pareto_values = pd.DataFrame({'f1': f1_l, 'f2': f2_l})
