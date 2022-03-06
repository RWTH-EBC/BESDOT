import os
import warnings
import pandas as pd
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.Component import Component

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))

unit_switch = 1000  # W/kWh


class SolarThermalCollectorFluid(FluidComponent):

    def __init__(self, comp_name, temp_profile, irr_profile,
                 comp_type='SolarThermalCollectorFluid', comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.inputs = ['solar']
        self.outputs = ['heat']
        self.temp_profile = temp_profile
        self.irr_profile = irr_profile
        # todo: (qli) solar_liquid_heat_cap korrigieren
        self.solar_liquid_heat_cap = 4180  # J/kgK
        self.unit_switch = 3600 * 1000  # J/kWh
        self.max_temp = 135

    def _constraint_temp(self, model):
        outlet_temp = model.find_component('outlet_temp_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in model.time_step:
                model.cons.add(outlet_temp[t] == t_out[t])
                model.cons.add(t_in[t] == inlet_temp[t])
                # todo: Regelung (GDP)
                '''
                if outlet_temp[t] - inlet_temp[t] >= 5:
                    model.cons.add(status[t] == 1)
                else:
                    model.cons.add(status[t] == 0)
                model.cons.add(output_energy[t] == output_energy[t] * status[t])
                '''
                # Über die max. Temperatur verdampft die Solarflüssigkeit.
                model.cons.add(outlet_temp[t] <= self.max_temp)

    """
    def _constraint_efficiency(self, model):
        eff = model.find_component('eff_' + self.name)
        solar_coll_properties_path = os.path.join(base_path, "data",
                                                  "component_database",
                                                  "SolarThermalCollectorFluid",
                                                  "FPC.csv")
        solar_coll_properties = pd.read_csv(solar_coll_properties_path)
        if 'optical_eff' in solar_coll_properties.columns:
            self.OpticalEfficiency = float(solar_coll_properties['optical_eff'])
        else:
            warnings.warn(
                "In the model database for " + self.component_type +
                " lack of column for optical efficiency.")
        if 'K' in solar_coll_properties.columns:
            self.K = float(solar_coll_properties['K'])
        else:
            warnings.warn(
                "In the model database for " + self.component_type +
                " lack of column for K.")
        outlet_temp = model.find_component('outlet_temp_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)

        for t in model.time_step:
            model.cons.add(
                eff[t] == self.OpticalEfficiency - self.K * ((inlet_temp[t] + 
                outlet_temp[t]) / 2 - self.temp_profile[t - 1]) / 
                self.irr_profile[t - 1])

    """

    # Test
    def _constraint_efficiency(self, model):
        eff = model.find_component('eff_' + self.name)
        for t in model.time_step:
            model.cons.add(eff[t] == 0.8)


    # 'size' bezieht sich auf die Fläche der Solarthermie.
    def _constraint_conver(self, model):
        eff = model.find_component('eff_' + self.name)
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        comp_size = model.find_component('size_' + self.name)
        for t in model.time_step:
            model.cons.add(input_energy[t] == self.irr_profile[t - 1] * eff[
                t] * comp_size / unit_switch)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        for heat_output in self.heat_flows_out:
            m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'mass')
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in model.time_step:
                # Beim Stagnationszustand gilt output_energy< input_energy
                model.cons.add(output_energy[t] <= input_energy[t])
                # model.cons.add(0 <= input_energy[t])
                # model.cons.add(0 <= output_energy[t])
                model.cons.add(
                    output_energy[t] == self.solar_liquid_heat_cap * (
                            m_out[t] * t_out[t] - m_in[t] * t_in[t]) /
                    self.unit_switch)

    def add_cons(self, model):
        self._constraint_vdi2067(model)
        self._constraint_temp(model)
        self._constraint_efficiency(model)
        self._constraint_conver(model)

    def add_vars(self, model):
        super().add_vars(model)

        inlet_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('inlet_temp_' + self.name, inlet_temp)

        outlet_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('outlet_temp_' + self.name, outlet_temp)

        eff = pyo.Var(model.time_step, bounds=(0, 1))
        model.add_component('eff_' + self.name, eff)
