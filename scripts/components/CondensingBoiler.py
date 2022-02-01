import os
import pyomo.environ as pyo
from scripts.components.GasBoiler import GasBoiler
import warnings
from tools.calc_exhaust_gas_loss import calc_exhaust_gas_loss
import pandas as pd
from scripts.FluidComponent import FluidComponent

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
path = os.path.join(base_path, "data", "component_database",
                               "CondensingBoiler", "BOI1_exhaust_gas.csv")
output_path = os.path.join(base_path, "data", "component_database",
                               "CondensingBoiler", "BOI1_exhaust_gas_loss.csv")


class CondensingBoiler(FluidComponent, GasBoiler):
    def __init__(self, comp_name, comp_type="CondensingBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.exhaust_gas_loss = calc_exhaust_gas_loss(path, output_path)

    def _constraint_conver(self, model):
        """
        Compared with _constraint_conver, this function turn the pure power
        equation into an equation, which consider the temperature of output
        flows and input flows.
        Before using temperature in energy conservation equation,
        the temperature properties of storage should be defined in
        _read_temp_properties.
        Returns
        -------

        """
        water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
        water_density = 1000  # kg/m3
        unit_switch = 3600 * 1000  # J/kWh
        # Taschenbuch für Heizungund Klimatechnik einschließlich Trinkwasser-
        # und Kältetechnik sowie Energiekonzepte, Herausgegeben von
        # Prof. Dr.-Ing. Karl-Josef Albers Hochschule Esslingen
        radiation_loss = 1  # %
        gas_calorific_value_high = 10.4  # kWh/m3
        gas_calorific_value_low = 8.9  # kWh/m3
        gas_calorific_high_value_high = 11.5  # kWh/m3
        gas_calorific_high_value_low = 9.8  # kWh/m3
        condensation_water_mass_high = 1.63  # kg/m3
        condensation_water_mass_low = 1.53  # kg/m3

        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        size = model.find_component('size_' + self.name)

        temp_var = model.find_component('temp_' + self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)
        condensation_heat = model.find_component('condensation_heat_' +
                                                 self.name)
        condensation_mass = model.find_component('condensation_mass_' +
                                                 self.name)
        self.loss = 0
        for t in range(len(model.time_step)):
            model.cons.add(output_energy[t + 1] <= size)
            model.cons.add(output_energy[t + 1] >= 0.3 * size)
            # Calculate the mass of condensate from the combustion power
            self.loss = self.exhaust_gas_loss + radiation_loss
            model.cons.add(input_energy[t + 1] ==
                           gas_calorific_high_value_low *
                           condensation_mass[t + 1] /
                           condensation_water_mass_low)
        for t in range(len(model.time_step) - 1):
            model.cons.add((input_energy[t + 2] + condensation_heat[t + 1]) *
                           (100 - self.loss) == output_energy[t + 2] * 100)
        # The temperature of the uncondensed gas, which is assumed to be 160
        # degrees according to the lesson, then it is condensed to below the
        # return temperature, thus obtaining the heat of condensation.
        for t in range(len(model.time_step)):
            model.cons.add(condensation_heat[t + 1] * unit_switch ==
                           water_heat_cap * condensation_mass[t + 1] *
                           (160 - return_temp_var[t + 1]))

    # todo(yca): init_temp is too high, think about it.
    def _constraint_temp(self, model, init_temp=60):
        temp_var = model.find_component('temp_' + self.name)
        model.cons.add(temp_var[1] == init_temp)
        for heat_output in self.heat_flows_out:
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])

    def _constraint_return_temp(self, model, init_return_temp=30):
        return_temp_var = model.find_component('return_temp_' + self.name)
        for t in model.time_step:
            model.cons.add(return_temp_var[t] == init_return_temp)
            model.cons.add(return_temp_var[t] <= 55)
        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(return_temp_var[t + 1] == t_in[t + 1])

    def _constraint_mass_flow(self, model):
        for heat_output in self.heat_flows_out:
            m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'mass')
            for t in range(len(model.time_step)):
                model.cons.add(m_in[t + 1] == m_out[t + 1])
                #model.cons.add(m_in[t + 1] == mass_flow)

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_temp(model)
        self._constraint_return_temp(model)
        self._constraint_vdi2067(model)
        self._constraint_mass_flow(model)
        self._constraint_heat_outputs(model)

    def add_vars(self, model):
        super().add_vars(model)

        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        return_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('return_temp_' + self.name, return_temp)

        condensation_heat = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('condensation_heat_' + self.name, condensation_heat)

        condensation_mass = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('condensation_mass_' + self.name, condensation_mass)


