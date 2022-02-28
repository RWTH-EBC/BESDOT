import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent


class ThreeWayValve(FluidComponent):

    def __init__(self, comp_name, comp_type="ThreeWayValve", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['heat']
        self.outputs = ['heat']
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_temp(self, model):
        mix_mass = model.find_component('mix_mass_' + self.name)
        inlet_hot_mass = model.find_component('inlet_hot_mass_' + self.name)
        inlet_cool_mass = model.find_component('inlet_cool_mass_' + self.name)
        outlet_hot_mass = model.find_component('outlet_hot_mass_' + self.name)
        outlet_cool_mass = model.find_component('outlet_cool_mass_' + self.name)
        mix_temp = model.find_component('mix_temp_' + self.name)
        inlet_hot_temp = model.find_component('inlet_hot_temp_' + self.name)
        inlet_cool_temp = model.find_component('inlet_cool_temp_' + self.name)
        outlet_hot_temp = model.find_component('outlet_hot_temp_' + self.name)
        outlet_cool_temp = model.find_component('outlet_cool_temp_' + self.name)
        for heat_input in self.heat_flows_in:
            m_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                        '_' + 'mass')
            t_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                         '_' + 'temp')
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(inlet_hot_temp[t + 1] == t_in[t + 1])
                model.cons.add(outlet_cool_temp[t + 1] == t_out[t + 1])
                model.cons.add(inlet_hot_mass[t + 1] == m_in[t + 1])
                model.cons.add(outlet_cool_mass[t + 1] == m_out[t + 1])

        for heat_output in self.heat_flows_out:
            m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'mass')
            t_in = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(outlet_hot_temp[t + 1] == t_out[t + 1])
                model.cons.add(inlet_cool_temp[t + 1] == t_in[t + 1])
                model.cons.add(outlet_hot_mass[t + 1] == m_out[t + 1])
                model.cons.add(inlet_cool_mass[t + 1] == m_in[t + 1])

        for t in range(len(model.time_step)):
            model.cons.add(inlet_hot_mass[t + 1] == outlet_cool_mass[t + 1])
            model.cons.add(outlet_hot_mass[t + 1] == inlet_cool_mass[t + 1])
            model.cons.add(inlet_hot_mass[t + 1] + mix_mass[t + 1] ==
                           outlet_hot_mass[t + 1])
            model.cons.add(outlet_cool_mass[t + 1] + mix_mass[t + 1] ==
                           inlet_cool_mass[t + 1])
            model.cons.add(mix_temp[t + 1] * mix_mass[t + 1] +
                           inlet_hot_mass[t + 1] * inlet_hot_temp[t + 1] ==
                           outlet_hot_mass[t + 1] * outlet_hot_temp[t + 1])

    def add_cons(self, model):
        self._constraint_temp(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        comp_size = pyo.Var(bounds=(self.min_size, self.max_size))
        model.add_component('size_' + self.name, comp_size)

        annual_cost = pyo.Var(bounds=(0, None))
        model.add_component('annual_cost_' + self.name, annual_cost)

        invest = pyo.Var(bounds=(0, None))
        model.add_component('invest_' + self.name, invest)

        mix_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('mix_temp_' + self.name, mix_temp)

        mix_mass = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('mix_mass_' + self.name, mix_mass)

        inlet_hot_mass = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('inlet_hot_mass' + self.name, inlet_hot_mass)

        inlet_cool_mass = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('inlet_cool_mass_' + self.name, inlet_cool_mass)

        outlet_hot_mass = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('outlet_hot_mass_' + self.name, outlet_hot_mass)

        outlet_cool_mass = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('outlet_cool_mass_' + self.name, outlet_cool_mass)

        inlet_hot_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('inlet_hot_temp_' + self.name, inlet_hot_temp)

        inlet_cool_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('inlet_cool_temp_' + self.name, inlet_cool_temp)

        outlet_hot_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('outlet_hot_temp_' + self.name, outlet_hot_temp)

        outlet_cool_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('outlet_cool_temp_' + self.name, outlet_cool_temp)





