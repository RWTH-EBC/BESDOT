# import warnings
# import pyomo.environ as pyo
# from pyomo.gdp import Disjunct, Disjunction
# from utils.calc_annuity_vdi2067 import calc_annuity
from scripts.Component import Component
# from utils.calc_exhaust_gas_loss import calc_exhaust_gas_loss
import os

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

small_num = 0.0001


class GasBoiler(Component):
    def __init__(self, comp_name, comp_type="GasBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['gas']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)


"""
    def _constraint_vdi2067(self, model):
        size = model.find_component('size_' + self.name)
        annual_cost = model.find_component('annual_cost_' + self.name)
        invest = model.find_component('invest_' + self.name)
        subsidy = 0

        if self.min_size == 0:
            min_size = small_num
        else:
            min_size = self.min_size

        if self.cost_model == 0:
            model.cons.add(size * self.unit_cost == invest)
        elif self.cost_model == 1:
            dis_not_select = Disjunct()
            not_select_size = pyo.Constraint(expr=size == 0)
            not_select_inv = pyo.Constraint(expr=invest == 0)
            model.add_component('dis_not_select_' + self.name, dis_not_select)
            dis_not_select.add_component('not_select_size_' + self.name,
                                         not_select_size)
            dis_not_select.add_component('not_select_inv_' + self.name,
                                         not_select_inv)

            dis_select = Disjunct()
            select_size = pyo.Constraint(expr=size >= min_size)
            select_inv = pyo.Constraint(expr=invest == size * self.unit_cost +
                                        self.fixed_cost)
            model.add_component('dis_select_' + self.name, dis_select)
            dis_select.add_component('select_size_' + self.name, select_size)
            dis_select.add_component('select_inv_' + self.name, select_inv)

            dj_size = Disjunction(expr=[dis_not_select, dis_select])
            model.add_component('disjunction_size' + self.name, dj_size)
        elif self.cost_model == 2:
            pair_nr = len(self.cost_pair)
            pair = Disjunct(pyo.RangeSet(pair_nr + 1))
            model.add_component(self.name + '_cost_pair', pair)
            pair_list = []
            for i in range(pair_nr):
                size_data = float(self.cost_pair[i].split(';')[0])
                price_data = float(self.cost_pair[i].split(';')[1])

                select_size = pyo.Constraint(expr=size == size_data)
                select_inv = pyo.Constraint(expr=invest == price_data)
                pair[i + 1].add_component(
                    self.name + 'select_size_' + str(i + 1),
                    select_size)
                pair[i + 1].add_component(
                    self.name + 'select_inv_' + str(i + 1),
                    select_inv)
                pair_list.append(pair[i + 1])

            select_size = pyo.Constraint(expr=size == 0)
            select_inv = pyo.Constraint(expr=invest == 0)
            pair[pair_nr + 1].add_component(self.name + 'select_size_' + str(0),
                                            select_size)
            pair[pair_nr + 1].add_component(self.name + 'select_inv_' + str(0),
                                            select_inv)
            pair_list.append(pair[pair_nr + 1])

            disj_size = Disjunction(expr=pair_list)
            model.add_component('disj_size_' + self.name, disj_size)

        annuity = calc_annuity(self.life, invest - subsidy, self.f_inst, self.f_w,
                               self.f_op)
        model.cons.add(annuity == annual_cost)
"""
