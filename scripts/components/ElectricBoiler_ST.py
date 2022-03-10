import os
import warnings

import pandas as pd
import pyomo.environ as pyo

from scripts.Component import Component

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))


class ElectricBoiler_ST(Component):

    def __init__(self, comp_name, comp_type="ElectricBoiler_ST",
                 comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['elec']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.heat_flows_in = []
        self.heat_flows_out = []

    def add_heat_flows(self, bld_heat_flows):
        for element in bld_heat_flows:
            if element[0] != 'e_grid' and element[1] != 'e_grid':
                if self.name == element[0]:
                    self.heat_flows_out.append(element)
                if self.name == element[1]:
                    self.heat_flows_in.append(element)

    def _constraint_bypass_flow(self, model):
        for heat_input in self.heat_flows_in:
            m_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'mass')
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            for heat_output in self.heat_flows_out:
                m_in = model.find_component(
                    heat_output[1] + '_' + heat_output[0] + '_' + 'mass')
                t_in = model.find_component(
                    heat_output[1] + '_' + heat_output[0] + '_' + 'temp')
                for t in model.time_step:
                    model.cons.add(m_out[t] == m_in[t])
                    model.cons.add(t_out[t] == t_in[t])

    def _constraint_heating_flow(self, model):
        for heat_input in self.heat_flows_in:
            m_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'mass')
            t_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'temp')
            for heat_output in self.heat_flows_out:
                m_out = model.find_component(
                    heat_output[0] + '_' + heat_output[1] + '_' + 'mass')
                t_out = model.find_component(
                    heat_output[0] + '_' + heat_output[1] + '_' + 'temp')
                for t in model.time_step:
                    model.cons.add(m_out[t] == m_in[t])
                    model.cons.add(t_out[t] >= t_in[t])

    def _constraint_conver(self, model):
        e_boi_properties_path = os.path.join(base_path, "data",
                                             "component_database",
                                             "ElectricBoiler_ST",
                                             "EB.csv")
        e_boi_properties = pd.read_csv(e_boi_properties_path)
        if 'efficiency' in e_boi_properties.columns:
            self.Efficiency = float(e_boi_properties['efficiency'])
        else:
            warnings.warn(
                "In the model database for " + self.component_type +
                " lack of column for efficiency.")

        water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
        unit_switch = 3600 * 1000  # J/kWh
        input_elec = model.find_component('input_elec_' + self.name)
        elec_transport = model.find_component('e_grid_' + self.name)
        input_heat = model.find_component('input_heat_' + self.name)
        heat_transport = model.find_component('water_tes_' + self.name)
        output_heat = model.find_component('output_heat_' + self.name)
        for t in model.time_step:
            model.cons.add(elec_transport[t] == input_elec[t])
            model.cons.add(heat_transport[t] == input_heat[t])
            model.cons.add(
                input_elec[t] * self.Efficiency + input_heat[t] == output_heat[
                    t])

        m_in = model.find_component('hw_cns_e_boi_' + 'mass')
        m_out = model.find_component('e_boi_hw_cns_' + 'mass')
        t_in = model.find_component('hw_cns_e_boi_' + 'temp')
        t_out = model.find_component('e_boi_hw_cns_' + 'temp')
        for t in model.time_step:
            model.cons.add(output_heat[t] == water_heat_cap * (
                        m_out[t] * t_out[t] - m_in[t] * t_in[t]) / unit_switch)

    def _constraint_maxpower(self, model):
        size = model.find_component('size_' + self.name)
        input_elec = model.find_component(
            'input_' + self.inputs[0] + '_' + self.name)
        for t in model.time_step:
            model.cons.add(input_elec[t] <= size)

    def add_cons(self, model):
        self._constraint_bypass_flow(model)
        self._constraint_heating_flow(model)
        self._constraint_conver(model)
        self._constraint_maxpower(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)

        input_heat = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('input_heat_' + self.name, input_heat)
