from scripts.Component import Component
import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.HeatExchangerFluid import HeatExchangerFluid
import math

area = 200


class UnderfloorHeat(HeatExchangerFluid):
    def __init__(self, comp_name, comp_type="UnderfloorHeat", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    # todo (yca): water_tes_under_heat is always constant,if massflow, temp and
    #  return temp were set.
    def _constraint_conver(self, model):
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)

        #for t in range(len(model.time_step) - 1):
        #    model.cons.add(input_energy[t + 1] >= output_energy[t + 1])

    def _constraint_temp(self, model, init_temp=30):
        temp_var = model.find_component('temp_' + self.name)
        for t in model.time_step:
            model.cons.add(temp_var[t] == init_temp)
        for heat_input in self.heat_flows_in:
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])

    # The total heat output of the underfloor heating can be calculated by the
    # above equation.
    # A: The area-specific heat output can be calculated on the room area.
    # q=8.92*(T_floor - T_air)^1.1
    # Q=q*A
    # todo(yca): area as variable combine with Building.
    def _constraint_floor_temp(self, model, room_temp=24):
        # todo (yca): this function is a highlight. Is it possible that the
        #  area is taken from Building object? if not, what is the challenge.
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        floor_temp = model.find_component('floor_temp_' + self.name)
        delta_t = model.find_component('delta_t_' + self.name)

        for t in range(len(model.time_step)):
            #model.cons.add(delta_t[t+1] == (floor_temp[t+1] - room_temp) **
            #               1.1)
            model.cons.add(delta_t[t + 1] == (floor_temp[t + 1] - room_temp))
            model.cons.add(output_energy[t+1] * 1000 == 8.92 * delta_t[t+1] *
                           area)

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_temp(model)
        self._constraint_mass_flow(model)
        self._constraint_heat_inputs(model)
        self._constraint_floor_temp(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)

        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        floor_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('floor_temp_' + self.name, floor_temp)

        delta_t = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('delta_t_' + self.name, delta_t)
