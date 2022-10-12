import pyomo.environ as pyo
from scripts.Component import Component
from tools.calc_annuity_vdi2067 import calc_annuity


class SolarThermalCollector(Component):

    def __init__(self, comp_name, temp_profile, irr_profile,
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

    def _constraint_area(self, model):
        """
        This constraint indicates the relationship between pv panel area in
        square meter and pv size in kWp. The nominal power is calculated
        according to the sunlight intensity of 1 kW/m².
        """
        area = model.find_component('solar_area_' + self.name)
        size = model.find_component('size_' + self.name)
        model.cons.add(size == area * 1 * self.efficiency['heat'])  # The 1 in
        # equation means the standard sunlight intensity of 1 kW/m²

    def _constraint_input(self, model):
        """
        This constraint indicates the relationship between panel area and the
        acceptable input energy.
        """
        input_powers = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        area = model.find_component('solar_area_' + self.name)
        for t in model.time_step:
            model.cons.add(input_powers[t] == area / 1000 * self.irr_profile[
                t - 1])
            # unit fo irradiance is W/m², should be changed to kW/m²

    def _constraint_vdi2067(self, model):
        """
        Compared to Component, the annual cost of solar thermal colleactor
        should be calculated with its area instead of the energy size in kWh.
        """
        area = model.find_component('solar_area_' + self.name)
        annual_cost = model.find_component('annual_cost_' + self.name)
        invest = model.find_component('invest_' + self.name)

        model.cons.add(area * self.unit_cost == invest)

        annuity = calc_annuity(self.life, invest, self.f_inst, self.f_w,
                               self.f_op)
        model.cons.add(annuity == annual_cost)

    def add_cons(self, model):
        super().add_cons(model)

        self._constraint_area(model)
        self._constraint_input(model)

    def add_vars(self, model):
        super().add_vars(model)

        area = pyo.Var(bounds=(0, None))
        model.add_component('solar_area_' + self.name, area)
