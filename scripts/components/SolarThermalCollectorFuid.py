import os
import warnings
import pandas as pd
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))


class SolarThermalCollectorFluid(FluidComponent):

    #  ??min_size=0, max_size=1000
    def __init__(self, comp_name, temp_profile, irr_profile,
                 comp_type="SolarThermalCollector", comp_model=None,
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
        self.solar_liquid_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
        self.unit_switch = 3600 * 1000  # J/kWh

    # def add_heat_flows(self, bld_heat_flows):
    #     for element in bld_heat_flows:
    #         if self.name == element[0]:
    #             self.heat_flows_out.append(element)
    #         if self.name == element[1]:
    #             self.heat_flows_in.append(element)

    def _constraint_irr_input(self, model):
        input_irr = model.find_component('input_irr_' + self.name)
        area = model.find_component('solar_area_' + self.name)
        for t in model.time_step:
            model.cons.add(
                input_irr[t] == area * self.irr_profile[t-1] / 1000)  # kWh

    def _constraint_efficiency(self, model):
        average_temp = model.find_component('average_temp_' + self.name)
        delta_temp = model.find_component('delta_temp_' + self.name)
        eff = model.find_component('eff_' + self.name)
        solar_coll_properties_path = os.path.join(base_path, "data",
                                                  "component_database",
                                                  "SolarThermalCollector",
                                                  "FlatPlateCollector.csv")
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
        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in model.time_step:
                model.cons.add(average_temp[t] == (t_in[t] + t_out[t]) / 2)
                model.cons.add(delta_temp[t] == average_temp[t] -
                               self.temp_profile[t])
                model.cons.add(
                    eff[t] == self.OpticalEfficiency - self.K * delta_temp[t])

    def _constraint_conver(self, model):
        input_irr = model.find_component('input_irr_' + self.name)
        eff = model.find_component('eff_' + self.name)
        input_energy = model.find_component('input_heat_' + self.name)
        for t in model.time_step:
            model.cons.add(input_energy[t] == input_irr[t] * eff[t])

    # todo: building.py anpassen
    def _constraint_heat_outputs(self, model):
        input_energy = model.find_component('input_heat_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        ctr_temp_diff = model.find_component('ctr_temp_diff_' + self.name)

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
                # todo: bld_8.water_tes_solar_coll_temp[t]
                model.cons.add(ctr_temp_diff[t] == t_out[t] - 20)
                # todo: Regelung
                if ctr_temp_diff[t] >= 5:
                    model.cons.add(output_energy[t] == input_energy[t])
                    model.cons.add(
                        output_energy[t] == self.solar_liquid_heat_cap * (
                                m_out[t] * t_out[t] - m_in[t] * t_in[
                            t]) * self.unit_switch)
                else:
                    model.cons.add(output_energy[t] == 0)
                model.cons.add(t_in[t] <= t_out[t])

    # todo: building.py anpassen
    def _constraint_temp(self, model):
        temp_var = model.find_component('temp_' + self.name)
        # todo: Ist return_temp auch eine Variable?
        # return_temp = model.find_component('return_temp_' + self.name)
        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in model.time_step:
                model.cons.add(temp_var[t] == t_out[t])
                model.cons.add(20 == t_in[t])

    def add_cons(self, model):
        # super().add_cons(model)
        self._constraint_vdi2067(model)
        self._constraint_irr_input(model)
        self._constraint_efficiency(model)
        self._constraint_heat_outputs(model)
        self._constraint_conver(model)
        self._constraint_temp(model)
        self._constraint_mass_flow(model)
        self._constraint_temp(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        # super().add_vars(model)

        comp_size = pyo.Var(bounds=(self.min_size, self.max_size))
        model.add_component('size_' + self.name, comp_size)

        annual_cost = pyo.Var(bounds=(0, None))
        model.add_component('annual_cost_' + self.name, annual_cost)

        invest = pyo.Var(bounds=(0, None))
        model.add_component('invest_' + self.name, invest)

        input_energy = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('input_' + self.inputs[0] + '_' + self.name,
                            input_energy)

        output_energy = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('output_' + self.outputs[0] + '_' + self.name,
                            output_energy)

        input_irr = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('input_irr_' + self.name, input_irr)

        area = pyo.Var(bounds=(0, None))
        model.add_component('solar_area_' + self.name, area)

        temp_var = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp_var)

        average_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('average_temp_' + self.name, average_temp)

        delta_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('delta_temp_' + self.name, delta_temp)

        eff = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('eff_' + self.name, eff)

        ctr_temp_diff = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('ctr_temp_diff_' + self.name, ctr_temp_diff)
