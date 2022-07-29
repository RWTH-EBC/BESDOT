import pyomo.environ as pyo
from scripts.components.Storage import Storage
from tools.calc_annuity_vdi2067 import calc_annuity

water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
water_density = 1000  # kg/m3
unit_switch = 3600 * 1000  # J/kWh


class HotWaterStorage(Storage):
    def __init__(self, comp_name, comp_type="HotWaterStorage",
                 comp_model=None, min_size=0, max_size=1000, current_size=0):
        self.inputs = ['heat']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.temp_diff = 60 # K

    # Attention! The size for hot water storage should be cubic meter instead
    # of kWh, since the key parameter for each product are given with the
    # volumen.
    def _constraint_volume(self, model):
        """
        This constraint indicates the relationship between storage volume in
        cubic meter and energy size in kWh
        """
        size = model.find_component('size_' + self.name)
        volume = model.find_component('volume_' + self.name)
        model.cons.add(size == volume * water_density * water_heat_cap *
                       self.temp_diff / unit_switch)

    def _constraint_vdi2067(self, model):
        """
        Compared to Component, the annual cost of hot water tank should be
        calculated with its volume instead of the energy size in kWh.
        """
        volume = model.find_component('volume_' + self.name)
        annual_cost = model.find_component('annual_cost_' + self.name)
        invest = model.find_component('invest_' + self.name)

        model.cons.add(volume * self.cost == invest)

        annuity = calc_annuity(self.life, invest, self.f_inst, self.f_w,
                               self.f_op)
        model.cons.add(annuity == annual_cost)

    def add_cons(self, model):
        super().add_cons(model)

        self._constraint_volume(model)

    def add_vars(self, model):
        """
        Compared to generic storage.
        """
        super().add_vars(model)

        # The unit for hot water storage in Topology and in calculation of
        # cost are cubic meter, so the maximal and minimal size of energy in
        # kWh should be modified.
        model.del_component('size_' + self.name)
        energy_size = pyo.Var(bounds=(0, None))
        model.add_component('size_' + self.name, energy_size)

        volume = pyo.Var(bounds=(self.min_size, self.max_size))
        model.add_component('volume_' + self.name, volume)
