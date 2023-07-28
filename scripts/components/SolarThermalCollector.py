import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Component import Component
from utils.calc_annuity_vdi2067 import calc_annuity

small_num = 0.0001


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
        # todo: change it into cost model 0,1,2
        area = model.find_component('solar_area_' + self.name)
        annual_cost = model.find_component('annual_cost_' + self.name)
        invest = model.find_component('invest_' + self.name)
        size = model.find_component('size_' + self.name)

        if self.min_size == 0:
            min_size = small_num
        else:
            min_size = self.min_size

        if self.cost_model == 0:
            model.cons.add(area * self.unit_cost == invest)
        elif self.cost_model == 1:
            dis_not_select = Disjunct()
            # area and size are connected by the function _constraint_area,
            # so the following constraint could be written in size or area.
            not_select_size = pyo.Constraint(expr=area == 0)
            not_select_inv = pyo.Constraint(expr=invest == 0)
            model.add_component('dis_not_select_' + self.name, dis_not_select)
            dis_not_select.add_component('not_select_size_' + self.name,
                                         not_select_size)
            dis_not_select.add_component('not_select_inv_' + self.name,
                                         not_select_inv)

            dis_select = Disjunct()
            select_size = pyo.Constraint(expr=area >= min_size /
                                              self.efficiency['heat'])
            # select_size_2 = pyo.Constraint(expr=area <= self.max_size /
            #                                   self.efficiency['heat'])
            select_inv = pyo.Constraint(expr=invest == area * self.unit_cost +
                                             self.fixed_cost)
            model.add_component('dis_select_' + self.name, dis_select)
            dis_select.add_component('select_size_' + self.name, select_size)
            # dis_select.add_component('select_size_2_' + self.name,
            #                          select_size_2)
            dis_select.add_component('select_inv_' + self.name, select_inv)

            dj_size = Disjunction(expr=[dis_not_select, dis_select])
            model.add_component('disjunction_size' + self.name, dj_size)
        elif self.cost_model == 2:
            pair_nr = len(self.cost_pair)
            pair = Disjunct(pyo.RangeSet(pair_nr + 1))
            model.add_component(self.name + '_cost_pair', pair)
            pair_list = []
            for i in range(pair_nr):
                area_data = float(self.cost_pair[i].split(';')[0])
                price_data = float(self.cost_pair[i].split(';')[1])

                select_area = pyo.Constraint(expr=area == area_data)
                select_inv = pyo.Constraint(expr=invest == price_data)
                pair[i + 1].add_component(
                    self.name + 'select_area_' + str(i + 1),
                    select_area)
                pair[i + 1].add_component(
                    self.name + 'select_inv_' + str(i + 1),
                    select_inv)
                pair_list.append(pair[i + 1])

            select_area = pyo.Constraint(expr=area == 0)
            select_inv = pyo.Constraint(expr=invest == 0)
            pair[pair_nr + 1].add_component(self.name + 'select_area_' + str(0),
                                            select_area)
            pair[pair_nr + 1].add_component(self.name + 'select_inv_' + str(0),
                                            select_inv)
            pair_list.append(pair[pair_nr + 1])

            disj_size = Disjunction(expr=pair_list)
            model.add_component('disj_size_' + self.name, disj_size)

        annuity = calc_annuity(self.life, invest, self.f_inst, self.f_w,
                               self.f_op)
        model.cons.add(annuity == annual_cost)

    def add_cons(self, model):
        # super().add_cons(model)
        self._constraint_vdi2067(model)
        self._constraint_conver(model)

        self._constraint_area(model)
        self._constraint_input(model)

    def add_vars(self, model):
        super().add_vars(model)

        min_area = self.min_size / 1 / self.efficiency['heat']
        max_area = self.max_size / 1 / self.efficiency['heat']

        area = pyo.Var(bounds=(min_area, max_area))
        model.add_component('solar_area_' + self.name, area)
