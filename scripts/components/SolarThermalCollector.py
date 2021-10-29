import pyomo.environ as pyo
from scripts.Component import Component


class SolarThermalCollector(Component):

    def __init__(self, comp_name, irr_profile,
                 comp_type="SolarThermalCollector", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['solar']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.irr_profile = irr_profile

    def _constraint_solar(self, model):
        input_powers = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        area = model.find_component('solar_area_' + self.name)

        for t in model.time_step:
            model.cons.add(input_powers[t] == area * self.irr_profile[t - 1] /
                           1000)
            # unit fo irradiance is W/m², should be changed to kW/m²

    def add_cons(self, model):
        super().add_cons(model)
        self._constraint_solar(model)

    def add_vars(self, model):
        super().add_vars(model)

        area = pyo.Var(bounds=(0, None))
        model.add_component('solar_area_' + self.name, area)
