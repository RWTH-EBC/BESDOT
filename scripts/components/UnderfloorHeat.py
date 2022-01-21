from scripts.Component import Component
import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
import math


class UnderfloorHeat(FluidComponent):
    def __init__(self, comp_name, comp_type="UnderfloorHeat", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_conver(self, model):
        pass

    def _constraint_temp(self, model, init_temp=30):
        # Initial temperature for water in storage is define with a constant
        # value.
        temp_var = model.find_component('temp_' + self.name)
        for t in model.time_step:
            model.cons.add(temp_var[t] == init_temp)
        for heat_input in self.heat_flows_in + self.heat_flows_out:
            t_out = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])

    def _constraint_floor_temp(self, model, area=200, room_temp=24):
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        floor_temp = model.find_component('floor_temp_' + self.name)
        delta_t = model.find_component('delta_t' + self.name)
        for t in range(len(model.time_step)):
            model.cons.add(delta_t[t+1] == (floor_temp[t+1] - room_temp) **
                           1.1)
            model.cons.add(output_energy[t+1] == 8.92 * delta_t[t+1] * area)

    def add_cons(self, model):
        self._constraint_temp(model)
        self._constraint_mass_flow(model)
        self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        # self._constraint_floor_temp(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)

        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        floor_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('foor_temp_' + self.name, floor_temp)

        delta_t = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('delta_T' + self.name, delta_t)
