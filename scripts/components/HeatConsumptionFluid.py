import os
import warnings

import pandas as pd
import pyomo.environ as pyo
from scripts.Component import Component
from scripts.FluidComponent import FluidComponent
from scripts.components import HeatConsumption

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))


class HeatConsumptionFluid(FluidComponent):

    def __init__(self, comp_name, consum_profile,
                 comp_type="HeatConsumptionFluid", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.consum_profile = consum_profile
        self.inlet_temp = None
        self.inputs = ['heat']

    def _constraint_maxpower(self, model):
        """
        The heat consumption has currently no max. power or investment
        constraint.
        """
        pass

    def _constraint_conver(self, model):
        """The input energy for Consumption should equal to the demand profil"""
        input_energy = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        for t in model.time_step:
            ####################################################################
            # ATTENTION!!! The time_step in pyomo is from 1 to 8760 and
            # python list is from 0 to 8759, so the index should be modified.
            ####################################################################
            model.cons.add(input_energy[t] == self.consum_profile[t - 1])

    # def add_variables(self, input_profiles, plant_parameters, var_dict, flows,
    #                   model, T):
    #
    #     output_flow = (self.name, 'therm_dmd')  # Define output flow
    #     flows['heat'][self.name][1].append(output_flow)  # Add output flow
    #
    #     var_dict[output_flow] = input_profiles['therm_demand']

    # todo (qli):
    def _constraint_heat_water_temp(self, model, init_temp=45):
        for heat_input in self.heat_flows_in:
            t_in = model.find_component(
                heat_input[0] + '_' + heat_input[1] + '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(init_temp == t_in[t + 1])

    # todo (qli):
    def _constraint_heat_water_return_temp(self, model, init_temp=18):
        for heat_input in self.heat_flows_in:
            t_out = model.find_component(
                heat_input[1] + '_' + heat_input[0] + '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(init_temp <= t_out[t + 1])

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_heat_water_temp(model)
        self._constraint_heat_water_return_temp(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)







