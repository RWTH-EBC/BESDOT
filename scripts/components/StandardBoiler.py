import os
import pyomo.environ as pyo
from scripts.components.GasBoiler import GasBoiler
import warnings
import pandas as pd
from tools.calc_exhaust_gas_loss import calc_exhaust_gas_loss
from scripts.FluidComponent import FluidComponent

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
path = os.path.join(base_path, "data", "component_database",
                               "StandardBoiler", "BOI_exhaust_gas.csv")
output_path = os.path.join(base_path, "data", "component_database",
                               "StandardBoiler", "BOI_exhaust_gas_loss.csv")


class StandardBoiler(FluidComponent, GasBoiler):
    def __init__(self, comp_name, comp_type="StandardBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         )
        self.heat_flows_in = None
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
        self.loss = 0
        # Taschenbuch für Heizungund Klimatechnik einschließlich Trinkwasser-
        # und Kältetechnik sowie Energiekonzepte, Herausgegeben von
        # Prof. Dr.-Ing. Karl-Josef Albers Hochschule Esslingen
        radiation_loss = 2  # %

        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        size = model.find_component('size_' + self.name)
        #modulation = model.find_component('modulation_' + self.name)
        self.loss = self.exhaust_gas_loss + radiation_loss

        for t in range(len(model.time_step)):
            model.cons.add(output_energy[t+1] <= size)
            model.cons.add(output_energy[t+1] >= 0.3 * size)
            #model.cons.add(modulation[t+1] == output_energy[t+1]/size)

            model.cons.add(input_energy[t+1] * (100 - self.loss) ==
                           output_energy[t+1] * 100)

    def _get_properties_loss(self, model):
        model_property_file = os.path.join(base_path, 'data',
                                           'component_database',
                                           'StandardBoiler',
                                           'BOI_exhaust_gas_loss.csv')
        properties = pd.read_csv(model_property_file)
        return properties

    def _read_properties_loss(self, properties):
        if 'exhaustgastemp' in properties.columns:
            self.exhaust_gas_temp = float(properties['exhaustgastemp'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for exhaustgas temperature.")

    def _constraint_temp(self, model, init_temp=80):
        temp_var = model.find_component('temp_' + self.name)
        for heat_output in self.heat_flows_out:
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])
                model.cons.add(temp_var[t + 1] == init_temp)

    def _constraint_mass_flow(self, model):
        for heat_output in self.heat_flows_out:
            m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'mass')
            for t in range(len(model.time_step)):
                model.cons.add(m_in[t + 1] == m_out[t + 1])

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_temp(model)
        self._constraint_vdi2067(model)
        self._constraint_mass_flow(model)
        self._constraint_heat_outputs(model)

    def add_vars(self, model):
        super().add_vars(model)

        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        return_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('return_temp_' + self.name, return_temp)

        #modulation = pyo.Var(model.time_step, bounds=(0, None))
        #model.add_component('modulation_' + self.name, modulation)




