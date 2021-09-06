"""
Simplified Modell for internal use.
"""

import pyomo.environ as pyo
import pandas as pd
import numpy as np
import os
import math


class Building(object):
    def __init__(self, name):
        """
        Initialization for building.
        :param name: name of the building, should be unique
        """
        self.name = name

        # Calculate the annual energy demand for heating, hot water and
        # electricity. Using TEK Tools from IWU.
        # todo: add methods to calculate the demand from building area
        self.annual_demand = {"elec_demand": 0,
                              "heat_demand": 0,
                              "cool_demand": 0,
                              "hot_water_demand": 0,
                              "gas_demand": 0}

        # todo: add methods to generate the energy demand profiles (electricity,
        #  heating and cooling)
        # The gas_demand is for natural gas, the demand of hydrogen is still not
        # considered in building.
        self.demand_profil = {"elec_demand": [],
                              "heat_demand": [],
                              "cool_demand": [],
                              "hot_water_demand": [],
                              "gas_demand": []}

    def add_profile(self, profile_dict):
        pass

    def __extract_results(self, save_local_file=False):
        # ToDo: also extract non time dependent variables (cycle variable) issubclass pyomo
        results_lst = []
        columns = ['TimeStep'] + [item for item in self.__input_profiles.keys() if item !='bsrn_irradiance'] + list(self.__var_dict.keys())
        for t in self.__time_steps:
            profile_lst = []
            for profile in self.__input_profiles:
                if profile != 'bsrn_irradiance':
                    profile_lst.append(self.__input_profiles[profile][t])
            local_lst = [t]+profile_lst  # self.__input_profiles['prices'][t]]
            for var in self.__var_dict:
                if issubclass(type(self.__var_dict[var]), dict) and issubclass(type(var), tuple):
                    local_lst.append(pyo.value(self.__var_dict[var][pd.Timestamp(t)]))
                elif issubclass(type(self.__var_dict[var]), pd.Series):
                    local_lst.append(self.__var_dict[var][t])
                elif issubclass(type(self.__var_dict[var]), pyo.Var):
                    local_lst.append(pyo.value(self.__var_dict[var]))
                else:  # issubclass(type(self.__var_dict[var]), float):
                    local_lst.append(self.__var_dict[var])
            results_lst.append(local_lst)
        # self.__model.solutions.load_from(self.__solver_result)
        if save_local_file:
            f = open("output_files/variable_result.txt", "w")
            for v in self.__model.component_objects(pyo.Var, active=True):
                f.write("Variable " + str(v))
                for index in v:
                    f.write("   " + str(index) + str(pyo.value(v[index])))
                    f.write("\n")
            f.close()

        return pd.DataFrame(np.array(results_lst), columns=columns)

