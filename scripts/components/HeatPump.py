import pyomo.environ as pyo
from scripts.Component import Component
import warnings
# from pyomo.gdp import Disjunct, Disjunction
# from utils.calc_annuity_vdi2067 import calc_annuity

small_num = 0.0001


class HeatPump(Component):

    def __init__(self, comp_name, temp_profile, comp_type="HeatPump",
                 comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        # Define inputs and outputs before the initialisation of component,
        # otherwise we can't read properties properly. By getting efficiency,
        # the energy typ is needed.
        self.inputs = ['elec']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.temp_profile = temp_profile

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if 'outlet temperature' in properties.columns:
            self.outlet_temp = float(properties['outlet temperature'])
        else:
            # warnings.warn("In the model database for " + self.component_type +
            #               " lack of column for outlet temperature.")
            print("In the model database for " + self.component_type +
                  " lack of column for outlet temperature. Default value is 50.")
            self.outlet_temp = 50

        # self.set_temp = 55

    def _constraint_cop(self, model):
        """
        Calculate the COP value in each time step, with default set
        temperature of 60 degree and machine efficiency of 40%.
        Setting COP as Parameter instead of Variable could reduce the
        complexity of mathematical model. Even from non-convex model into
        convex model.
        """
        # The cop_list could only be defined with dict, list is not possible
        # for pyomo 6.0. The reason is the unmatched index in pyomo and python
        cop_list = {}
        for t in model.time_step:
            cop_list[t] = (self.outlet_temp + 273.15) * self.efficiency[
                self.outputs[0]] / (self.outlet_temp - self.temp_profile[t - 1])

        cop = pyo.Param(model.time_step, initialize=cop_list)
        # import numpy as np
        # print("COP value is: ")
        # print(np.mean(list(cop_list.values())))
        model.add_component('cop_' + self.name, cop)

    def _constraint_conver(self, model):
        """
        Energy conservation equation for heat pump with variable COP value.
        Heat pump has only one input and one output, maybe? be caution for 5
        generation heat network.
        """
        input_powers = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        output_powers = model.find_component('output_' + self.outputs[0] + '_' +
                                             self.name)
        cop = model.find_component('cop_' + self.name)
        for t in model.time_step:
            model.cons.add(output_powers[t] == input_powers[t] * cop[t])

    def add_cons(self, model):
        self._constraint_cop(model)
        super().add_cons(model)
