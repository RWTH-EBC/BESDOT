"""
Simplified Modell for internal use.
"""

import os
from warnings import warn
import pyomo.environ as pyo
import pandas as pd
import numpy as np
import tsam.timeseriesaggregation as tsam
from tools.k_medoids import cluster

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

        # Infos about time series cluster, default value set to False
        self.cluster = None

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

    def time_cluster(self, nr_periods=12, hours_period=24):
        # The profiles could be clustered are: demand profiles, weather
        # profiles and prices profiles (if necessary). demand profiles are
        # stored in buildings and other information are stored in Environment
        # objects.
        # todo (yni): the cluster is developed only for whole year scenarios.
        #  Whether to adapt to other scenarios needs further consideration.
        if self.environment is None:
            warn("Can't find Environment object in Project")
        if self.environment.time_step != 8760:
            warn("The time_cluster is developed only for whole year scenarios")
        if len(self.building_list) == 0:
            warn("Can't find Building object in Project")
        elif len(self.building_list) > 1:
            warn("Number of Building object in Project is larger than 1")

        demand_profiles = self.building_list[0].demand_profile
        weather_profiles = {"temp": self.environment.temp_profile,
                            "wind": self.environment.wind_profile,
                            "irr": self.environment.irr_profile}
        price_profiles = {}
        if isinstance(self.environment.elec_price, list):
            price_profiles["elec_price"] = self.environment.elec_price
        if isinstance(self.environment.elec_price, list):
            price_profiles["gas_price"] = self.environment.elec_price
        if isinstance(self.environment.elec_price, list):
            price_profiles["heat_price"] = self.environment.elec_price
        if isinstance(self.environment.elec_price, list):
            price_profiles["elec_feed_price"] = self.environment.elec_price
        if isinstance(self.environment.elec_price, list):
            price_profiles["co2_price"] = self.environment.elec_price

        # Original profiles for mentioned series
        orig_profiles = {**demand_profiles, **weather_profiles,
                         **price_profiles}

        # Delete empty elements before clustering
        empty_element_list = []
        for key in orig_profiles.keys():
            if len(orig_profiles[key]) == 0:
                empty_element_list.append(key)

        for empty_element in empty_element_list:
            del orig_profiles[empty_element]

        # Turn profiles from dict into pandas Dataframe and use package tsam
        raw = pd.DataFrame(orig_profiles)
        raw.index = pd.to_datetime(arg=raw.index, unit='h',
                                   origin=pd.Timestamp('2021-01-01'))

        aggregation = \
            tsam.TimeSeriesAggregation(raw,
                                       noTypicalPeriods=nr_periods,
                                       hoursPerPeriod=hours_period,
                                       clusterMethod='hierarchical',
                                       extremePeriodMethod='new_cluster_center',
                                       addPeakMin=['temp'],
                                       addPeakMax=['heat_demand'])
        typ_periods = aggregation.createTypicalPeriods()
        print('######')
        print(typ_periods)
        predicted_periods = aggregation.predictOriginalData()
        print('######')
        print(predicted_periods)

        self.cluster = aggregation

    def build_model(self, obj_typ='annual_cost'):
        """
        Build up a mathematical model (concrete model) using pyomo modeling
        language for optimization.
        """
        if self.typ == 'building' and len(self.building_list) == 1:
            # Initialisation of ConcreteModel
            self.model = pyo.ConcreteModel(self.name)
            self.model.cons = pyo.ConstraintList()

            if self.cluster is None:
                self.model.time_step = pyo.RangeSet(self.environment.time_step)

                # # Assign pyomo variables
                # bld = self.building_list[0]
                # bld.add_vars(self.model)
                #
                # # Add pyomo constraints to model
                # bld.add_cons(self.model, self.environment)
            else:
                # The reduced data are stored in clusterPeriodDict as dict,
                # the keys are the items, which are used for clustering such
                # as demand profiles and weather profiles.
                print(len(list(self.cluster.clusterPeriodDict.values())[0]))
                self.model.time_step = pyo.RangeSet(len(list(
                    self.cluster.clusterPeriodDict.values())[0]))

            # Assign pyomo variables
            bld = self.building_list[0]
            bld.add_vars(self.model)

            # Add pyomo constraints to model
            bld.add_cons(self.model, self.environment, self.cluster)

            # Add pyomo objective
            bld_annual_cost = self.model.find_component('annual_cost_' +
                                                        bld.name)
            bld_operation_cost = self.model.find_component(
                'operation_cost_' + bld.name)

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
        #pyo.TransformationFactory('gdp.chull').apply_to(self.model)
        solver = pyo.SolverFactory(solver_name)
        # Attention! The option was set for the dimension optimization for
        # HomoStorage
        solver.options['NonConvex'] = 2
        solver.options['MIPGap'] = 1

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
