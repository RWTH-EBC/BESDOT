from scripts.Component import Component
import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.HeatExchangerFluid import HeatExchangerFluid
import math


class Radiator(HeatExchangerFluid):
    def __init__(self, comp_name, comp_type="Radiator", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_conver(self, model):
        pass

    def _constraint_temp(self, model):
        # Initial temperature for water in storage is define with a constant
        # value.
        temp_var = model.find_component('temp_' + self.name)
        model.cons.add(temp_var[1] == init_temp)

        for heat_input in self.heat_flows_in:
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])

        for heat_output in self.heat_flows_out:
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])

    def _constraint_return_temp(self, model, init_temp=20):
        # The first constraint for return temperature. Assuming a constant
        # temperature difference between flow temperature and return
        # temperature.
        return_temp_var = model.find_component('return_temp_' + self.name)
        for t in model.time_step:
            model.cons.add(return_temp_var[t] == init_temp)
        for heat_input in self.heat_flows_in:
            t_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(return_temp_var[t + 1] == t_in[t + 1])

        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(return_temp_var[t + 1] == t_in[t + 1])

    def add_cons(self, model):
        self._constraint_conver(model)
        # self._constraint_temp(model)
        self._constraint_mass_flow(model)
        self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        self._constraint_vdi2067(model)

    # def add_variables(self, input_parameters, plant_parameters, var_dict, flows,
    #                   *args):
    #     # todo: consider "heat_demand" as a new constraint
    #     output_flow = (self.name, 'therm_dmd')  # Define output flow
    #     flows['heat'][self.name][1].append(output_flow)  # Add output flow
    #
    #     var_dict[output_flow] = input_parameters['therm_demand']  # Assign
    #     # values to output flow in the var_dict
