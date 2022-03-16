"""
Simplified Modell for internal use.
"""

import os
from warnings import warn
import pyomo.environ as pyo
import pandas as pd
import numpy as np


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Project(object):
    def __init__(self, name, typ):
        self.name = name
        self.typ = typ

        # The following attributs should be replaced or added with related
        # object before generating pyomo model.
        self.environment = None
        self.district_list = []
        self.building_list = []

        # The pyomo model
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

    def build_model(self, obj_typ='annual_cost'):
        """
        Build up a mathematical model (concrete model) using pyomo modeling
        language for optimization.
        """
        if self.typ == 'building' and len(self.building_list) == 1:
            # Initialisation of ConcreteModel
            self.model = pyo.ConcreteModel(self.name)
            self.model.time_step = pyo.RangeSet(self.environment.time_step)
            self.model.cons = pyo.ConstraintList()

            # Assign pyomo variables
            bld = self.building_list[0]
            bld.add_vars(self.model)

            # Add pyomo constraints to model
            bld.add_cons(self.model, self.environment)

            # Add pyomo objective
            bld_annual_cost = self.model.find_component('annual_cost_' +
                                                        bld.name)
            bld_operation_cost = self.model.find_component('operation_cost_' +
                                                           bld.name)

            # If objective is annual cost, the components size should be
            # given in range, so that the dimensioning could be made. If
            # objective is operation cost, the components size should be
            # given with the same size of maximal and minimal size.

            if obj_typ == 'annual_cost':
                self.model.obj = pyo.Objective(expr=bld_annual_cost,
                                               sense=pyo.minimize)
            elif obj_typ == 'operation_cost':
                self.model.obj = pyo.Objective(expr=bld_operation_cost,
                                               sense=pyo.minimize)
            else:
                warn('The obj_typ is not allowed. The allowed typ is '
                     'annual_cost or operation_cost')
        else:
            print("Other project application scenario haven't been developed")

    def run_optimization(self, solver_name='gurobi', save_lp=False,
                         save_result=False):
        """
        solver.options['Heuristics'] = 0.05
        solver.options['MIPGap'] = 0.01
        solver.options['ImproveStartGap'] = 0.04
        solver.options['MIPFocus'] = 3  # 1
        solver.options['Presolve'] = 2  # this can be helpful!
        solver.options['NumericFocus'] = 1
        solver.options['NonConvex'] = 2  # only for gurobi nlp

        solvers:
        glpk(bad for milp), cbc(good for milp), gurobi: linear, ipopt: nonlinear
        """
        pyo.TransformationFactory('gdp.bigm').apply_to(self.model)
        solver = pyo.SolverFactory(solver_name)
        # Attention! The option was set for the dimension optimization for
        # HomoStorage
        solver.options['NonConvex'] = 2

        opt_result = solver.solve(self.model, tee=True)

        # Save model in lp file, this only works with linear model. That is
        # not necessary.
        if save_lp:
            model_output_path = os.path.join(base_path, 'data', 'opt_output',
                                             self.name + '_model.lp')
            self.model.write(model_output_path,
                             io_options={'symbolic_solver_labels': True})

        # Save results in csv file.
        if save_result:
            result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                              self.name + '_result.csv')

            # Get results for all variable. This is VERY slow.
            # todo (yni): find an more efficient way to save results
            result_dict = {}
            for v in self.model.component_objects(pyo.Var, active=True):
                # print("Variable component object",v)
                for index in v:
                    # print("   ", v[index], v[index].value)
                    result_dict[str(v[index])] = v[index].value
            result_df = pd.DataFrame(result_dict.items(), columns=['var',
                                                                   'value'])
            result_df.to_csv(result_output_path)

            # Get value of single variable
            # print(self.model.size_pv.value)




