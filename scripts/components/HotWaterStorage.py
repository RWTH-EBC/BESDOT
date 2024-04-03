import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.components.Storage import Storage
from utils.calc_annuity_vdi2067 import calc_annuity

water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
water_density = 1  # kg/Liter
unit_switch = 3600 * 1000  # J/kWh
small_num = 0.0001


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

        self.temp_diff = 60  # K
        self.set_init = True

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
        city_subsidy = model.find_component('city_subsidy_' + self.name)
        state_subsidy = model.find_component('state_subsidy_' + self.name)
        country_subsidy = model.find_component('country_subsidy_' + self.name)

        # Take the fixed cost for investment into account and use dgp model to
        # indicate that, if component size is equal to zero, the investment
        # equal to zero as well. If component size is lager than zero,
        # the fixed cost should be considered.
        # The small number is given because "larger" is not allowed for
        # optimization language, so use "larger equal to" replace "larger"
        # with a small number. If min size is given from the model database,
        # the small number is no more necessary.

        if self.min_size == 0:
            min_size = small_num
        else:
            min_size = self.min_size

        if self.cost_model == 0:
            model.cons.add(volume * self.unit_cost == invest)
        elif self.cost_model == 1:
            dis_not_select = Disjunct()
            not_select_size = pyo.Constraint(expr=volume == 0)
            not_select_inv = pyo.Constraint(expr=invest == 0)
            model.add_component('dis_not_select_' + self.name, dis_not_select)
            dis_not_select.add_component('not_select_size_' + self.name,
                                         not_select_size)
            dis_not_select.add_component('not_select_inv_' + self.name,
                                         not_select_inv)

            dis_select = Disjunct()
            select_size = pyo.Constraint(expr=volume >= min_size)
            select_inv = pyo.Constraint(expr=invest == volume *
                                        self.unit_cost + self.fixed_cost)
            model.add_component('dis_select_' + self.name, dis_select)
            dis_select.add_component('select_size_' + self.name,
                                     select_size)
            dis_select.add_component('select_inv_' + self.name,
                                     select_inv)

            dj_size = Disjunction(expr=[dis_not_select, dis_select])
            model.add_component('disjunction_size' + self.name, dj_size)
        elif self.cost_model == 2:
            pair_nr = len(self.cost_pair)
            pair = Disjunct(pyo.RangeSet(pair_nr + 1))
            model.add_component(self.name + '_cost_pair', pair)
            pair_list = []
            for i in range(pair_nr):
                volume_data = float(self.cost_pair[i].split(';')[0])
                price_data = float(self.cost_pair[i].split(';')[1])

                select_size = pyo.Constraint(expr=volume == volume_data)
                select_inv = pyo.Constraint(expr=invest == price_data)
                pair[i + 1].add_component(
                    self.name + 'select_size_' + str(i + 1),
                    select_size)
                pair[i + 1].add_component(
                    self.name + 'select_inv_' + str(i + 1),
                    select_inv)
                pair_list.append(pair[i + 1])

            select_size = pyo.Constraint(expr=volume == 0)
            select_inv = pyo.Constraint(expr=invest == 0)
            pair[pair_nr + 1].add_component(self.name + 'select_size_' + str(0),
                                            select_size)
            pair[pair_nr + 1].add_component(self.name + 'select_inv_' + str(0),
                                            select_inv)
            pair_list.append(pair[pair_nr + 1])

            disj_size = Disjunction(expr=pair_list)
            model.add_component('disj_size_' + self.name, disj_size)

        annuity = calc_annuity(self.life, invest, self.f_inst, self.f_w, self.f_op)
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
        model.add_component('size_' + self.name, energy_size)  # unit in kWh

        volume = pyo.Var(bounds=(self.min_size, self.max_size))
        model.add_component('volume_' + self.name, volume)  # unit in Liter
