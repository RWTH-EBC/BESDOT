from scripts.Component import Component
import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.HeatExchangerFluid import HeatExchangerFluid
import math
water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
water_density = 1000  # kg/m3
unit_switch = 3600 * 1000  # J/kWh


class Radiator(HeatExchangerFluid, FluidComponent):
    def __init__(self, comp_name, comp_type="Radiator", comp_model=None,
                 min_size=0, max_size=1000, current_size=0, over_temp_n=49.8):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        # According to EN 442, the standard output of radiators is specified at
        # 75/65/20 °C, i.e. at tV = 75 °C (flow), tR = 65 °C (return) and tL =
        # 20 °C (room air) and at the usual atmospheric pressure (1013 mbar).
        # The standard overtemperature was calculated from the log-average
        # formula.(49.8)
        self.over_temp_n = over_temp_n

    # todo(yca):same as underfloorheat.
    # todo(yca): NO FUNCTION of Q = C * M * DELTA T
    def _constraint_conver(self, model, room_temp=24, area=200):
        temp_var = model.find_component('temp_' + self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)
        temp_difference = model.find_component('temp_difference_' + self.name)
        conversion_factor = model.find_component('conversion_factor_' +
                                                 self.name)
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)

        for t in range(len(model.time_step)):
            model.cons.add(temp_difference[t + 1] == (temp_var[t + 1] +
                                                      return_temp_var[t + 1] - 2
                                                      * room_temp) / 2)
            # model.cons.add(conversion_factor[t + 1] == (self.over_temp_n /
            #                                            temp_difference[t + 1])
            #               ** 1.3)
            # todo: the meaning of following equation
             #model.cons.add(input_energy[t + 1] >= output_energy[t + 1] *
             #              conversion_factor[t + 1])
            model.cons.add(input_energy[t + 1] >= output_energy[t + 1] * 1.1)
            model.cons.add(output_energy[t + 1] * 1000 == self.k * area *
                           temp_difference[t + 1])

    def _read_properties(self, properties):
        super()._read_properties(properties)

    def _constraint_temp(self, model, init_temp=40):
        temp_var = model.find_component('temp_' + self.name)
        for t in model.time_step:  # todo(yca): do this syntax work?
            # todo (yca): same as underfloorheat
            model.cons.add(temp_var[t] == init_temp)
        for heat_input in self.heat_flows_in:
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])

    def _constraint_return_temp(self, model):
        return_temp_var = model.find_component('return_temp_' + self.name)

        for heat_output in self.heat_flows_in:
            t_in = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                        '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(return_temp_var[t + 1] == t_in[t + 1])

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_temp(model)
        #self._constraint_return_temp(model)
        self._constraint_mass_flow(model)
        self._constraint_heat_inputs(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)

        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        return_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('return_temp_' + self.name, return_temp)

        temp_difference = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_difference_' + self.name, temp_difference)

        conversion_factor = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('conversion_factor_' + self.name, conversion_factor)
    # def add_variables(self, input_parameters, plant_parameters, var_dict, flows,
    #                   *args):
    #     # todo: consider "heat_demand" as a new constraint
    #     output_flow = (self.name, 'therm_dmd')  # Define output flow
    #     flows['heat'][self.name][1].append(output_flow)  # Add output flow
    #
    #     var_dict[output_flow] = input_parameters['therm_demand']  # Assign
    #     # values to output flow in the var_dict
