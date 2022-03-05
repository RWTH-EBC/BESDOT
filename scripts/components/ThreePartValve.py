import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.HeatExchanger import HeatExchanger


class ThreePartValve(HeatExchanger, FluidComponent):
    def __init__(self, comp_name, comp_type="ThreePartValve",
                 comp_model=None, min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.efficiency['heat'] = 1

    def _constraint_temp(self, model):
        for heat_input in self.heat_flows_in:
            c_out_temp = model.find_component(
                heat_input[1] + '_' + heat_input[0] + '_' + 'temp')
        for heat_output in self.heat_flows_out:
            c_in_temp = model.find_component(heat_output[1] + '_' +
                                             heat_output[0] + '_' + 'temp')
        for t in model.time_step:
            model.cons.add(c_out_temp[t] == c_in_temp[t])

    def _constraint_mass(self, model):
        # 'size' des Dreiwegeventils  wird in m³/h angegeben.
        size = model.find_component('size_' + self.name)
        for heat_input in self.heat_flows_in:
            input_loop_mass = model.find_component(
                heat_input[0] + '_' + heat_input[1] + '_' + 'mass')
        for heat_output in self.heat_flows_out:
            output_loop_mass = model.find_component(
                heat_output[0] + '_' + heat_output[1] + '_' + 'mass')
        for t in model.time_step:
            model.cons.add(output_loop_mass[t] >= input_loop_mass[t])
            model.cons.add(output_loop_mass[t] <= size)

    def add_cons(self, model):
        self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        self._constraint_temp(model)
        self._constraint_mass(model)
        self._constraint_conver(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)
