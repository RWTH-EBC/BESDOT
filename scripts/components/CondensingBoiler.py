import os
import pyomo.environ as pyo
from scripts.components.GasBoiler import GasBoiler
import warnings
from tools.calc_exhaust_gas_loss import calc_exhaust_gas_loss

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
path = os.path.join(base_path, "data", "component_database",
                               "CondensingBoiler", "BOI1_exhaust_gas.csv")
output_path = os.path.join(base_path, "data", "component_database",
                               "CondensingBoiler", "BOI1_exhaust_gas_loss.csv")


class CondensingBoiler(GasBoiler):
    def __init__(self, comp_name, comp_type="CondensingBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

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
        # todo(yca):reference
        radiation_loss = 1 # %
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
        loss = model.find_component('loss_' + self.name)
        mass_flow_var = model.find_component('mass_flow_' + self.name)
        exhaust_gas_loss = model.find_component('exhaust_gas_loss_' + self.name)
        condensation_heat = model.find_component('condensation_heat_' +
                                                 self.name)
        condensation_mass = model.find_component('condensation_mass_' +
                                                 self.name)
        combustion_input = model.find_component('combustion_input_' +
                                                 self.name)
        #todo(yca):add condensation_heat and loss
        for t in range(len(model.time_step)):
            model.cons.add(output_energy[t + 1] ==
                           (temp_var[t + 1] - return_temp_var[t + 1]) *
                           mass_flow_var[t + 1] * water_heat_cap / unit_switch)
            model.cons.add(output_energy[t + 1] <= size)
            model.cons.add(output_energy[t + 1] >= 0.3 * size)
            #fixme(yca):unsupported operand type(s) for +: 'NoneType' and 'int'
            model.cons.add(loss == exhaust_gas_loss +
                           radiation_loss_coefficient)

            model.cons.add(combustion_input[t + 1] == input_energy[t + 1] /
                           loss)
            model.cons.add(combustion_input[t + 1] ==
                           gas_calorific_high_value_low *
                           condensation_mass[t + 1] /
                           condensation_water_mass_low)

    def _constraint_loss(self, model):
        exhaust_gas_loss = model.find_component('exhaust_gas_loss_' + self.name)
        exhaust_gas_loss = calc_exhaust_gas_loss(path, output_path)

    def _get_properties_loss(self, model):
        model_property_file = os.path.join(base_path, 'data',
                                           'component_database',
                                           'CondensingBoiler',
                                           'BOI1_exhaust_gas_loss.csv')
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
        for t in model.time_step:
            model.cons.add(temp_var[1] == init_temp)

    def _constraint_return_temp(self, model, init_return_temp=55):
        return_temp_var = model.find_component('return_temp_' + self.name)
        for t in model.time_step:
            model.cons.add(return_temp_var[t] == init_return_temp)
            model.cons.add(return_temp_var[t] <= 55)

    def _constraint_mass_flow(self, model, mass_flow=100):
        mass_flow_var = model.find_component('mass_flow_' + self.name)
        for t in model.time_step:
            model.cons.add(mass_flow_var[t] == mass_flow)

    #todo(yca): check taupunkt and mass of condensation water and constraint
    def _constraint_condensation_heat(self, model):
        water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
        unit_switch = 3600 * 1000  # J/kWh
        condensation_heat = model.find_component('condensation_heat' +
                                                 self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)
        condensation_mass = model.find_component('condensation_mass_' +
                                                 self.name)
        model.cons.add(condensation_heat[1] == 0)
        for t in range(len(model.time_step)):
            model.cons.add(condensation_heat[t + 1] == water_heat_cap *
                           condensation_mass[t + 1] * (self.exhaust_gas_temp -
                                                return_temp_var[t + 1]))

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_loss(model)
        self._constraint_temp(model)
        self._constraint_return_temp(model)
        self._constraint_vdi2067(model)
        self._constraint_mass_flow(model)

    def add_vars(self, model):
        super().add_vars(model)

        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        return_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('return_temp_' + self.name, return_temp)

        mass_flow = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('mass_flow_' + self.name, mass_flow)

        condensation_heat = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('condensation_heat_' + self.name, condensation_heat)

        condensation_mass = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('condensation_mass_' + self.name, condensation_mass)

        combustion_input = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('combustion_input_' + self.name, combustion_input)

