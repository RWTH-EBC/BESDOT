import os
import warnings

import pandas as pd
import pyomo.environ as pyo

from scripts.Component import Component
from scripts.FluidComponent import FluidComponent

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))


class ElectricBoiler_ST(FluidComponent):

    def __init__(self, comp_name, comp_type="ElectricBoiler_ST",
                 comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        # e_boi wird als ein spezieller WÜ mit elektrischer Heizung betrachtet.
        self.inputs = ['heat', 'elec']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_mass_temp(self, model):
        for heat_input in self.heat_flows_in:
            m_out_cold = model.find_component(
                heat_input[1] + '_' + heat_input[0] +
                '_' + 'mass')
            t_out_cold = model.find_component(
                heat_input[1] + '_' + heat_input[0] +
                '_' + 'temp')
            t_in_cold = model.find_component(
                heat_input[0] + '_' + heat_input[1] +
                '_' + 'temp')
            for heat_output in self.heat_flows_out:
                m_in_hot = model.find_component(
                    heat_output[1] + '_' + heat_output[0] + '_' + 'mass')
                t_in_hot = model.find_component(
                    heat_output[1] + '_' + heat_output[0] + '_' + 'temp')
                t_out_hot = model.find_component(
                    heat_output[0] + '_' + heat_output[1] + '_' + 'temp')
                for t in model.time_step:
                    model.cons.add(m_out_cold[t] == m_in_hot[t])
                    model.cons.add(t_out_cold[t] == t_in_hot[t])
                    model.cons.add(t_in_cold[t] <= t_out_hot[t])

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

        input_elec = model.find_component('input_elec_' + self.name)
        input_heat = model.find_component('input_heat_' + self.name)
        output_heat = model.find_component('output_heat_' + self.name)

        for t in model.time_step:
            model.cons.add(
                input_elec[t] * self.Efficiency + input_heat[t] == output_heat[
                    t])

    def add_cons(self, model):
        self._constraint_mass_temp(model)
        self._constraint_conver(model)
        self._constraint_maxpower(model)
        self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)
