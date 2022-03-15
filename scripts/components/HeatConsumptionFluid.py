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

    def _constraint_temp(self, model):
        heatCNS_properties_path = os.path.join(base_path, "data",
                                               "component_database",
                                               "HeatConsumptionFluid",
                                               "HeatCNS.csv")
        heatCNS_properties = pd.read_csv(heatCNS_properties_path)
        if 'inlet_temp' in heatCNS_properties.columns:
            self.inlet_temp = float(heatCNS_properties['inlet_temp'])
        else:
            warnings.warn(
                "In the model database for " + self.component_type +
                " lack of column for inlet temperature.")

        inlet_temp = model.find_component('inlet_temp_' + self.name)
        outlet_temp = model.find_component('outlet_temp_' + self.name)
        for heat_input in self.heat_flows_in + self.heat_flows_out:
            t_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            for t in model.time_step:
                model.cons.add(inlet_temp[t] == t_in[t])
                model.cons.add(outlet_temp[t] == t_out[t])
                model.cons.add(inlet_temp[t] >= self.inlet_temp)

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
        self._constraint_heat_inputs(model)
        self._constraint_temp(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)

        inlet_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('inlet_temp_' + self.name, inlet_temp)

        outlet_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('outlet_temp_' + self.name, outlet_temp)






