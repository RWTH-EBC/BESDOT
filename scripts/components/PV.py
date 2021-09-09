import warnings
import pyomo.environ as pyo
from scripts.Component import Component


class PV(Component):

    def __init__(self, comp_name, irr_profile, comp_type="PV", comp_model=None):
        self.inputs = ['solar']
        self.outputs = ['elec']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)

        self.irr_profile = irr_profile

    def _read_properties(self, properties):
        """
        The PV model utilizes additionally temperature coefficient and NOCT
        (Nominal Operating Cell Temperature) to calculate the pv factor,
        besides all universal properties
        """
        super()._read_properties(properties)
        if 'temp coefficient' in properties.columns:
            self.temp_coefficient = float(properties['temp coefficient'])
        elif 'temp_coefficient' in properties.columns:
            self.temp_coefficient = float(properties['temp_coefficient'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for temp coefficient")
        if 'NOCT' in properties.columns:
            self.noct = float(properties['NOCT'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for NOCT")

    def _constraint_solar(self, model):
        input_powers = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        area = model.find_component('solar_area_' + self.name)

        for t in model.time_step:
            model.cons.add(input_powers[t] == area / 1000 * self.irr_profile[
                t-1])
            # unit fo irradiance is W/m², should be changed to kW/m²

    def add_cons(self, model):
        super().add_cons(model)
        self._constraint_solar(model)

    def add_vars(self, model):
        super().add_vars(model)

        area = pyo.Var(bounds=(0, None))
        model.add_component('solar_area_' + self.name, area)


if __name__ == '__main__':
    pv = PV(comp_name='test_pv', irr_profile=[100, 200, 300], comp_type="PV",
            comp_model='PV1')
