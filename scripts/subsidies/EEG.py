import numpy as np
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction

from scripts.subsidies.OperateSubsidy import OperateSubsidy


small_num = 0.0001


class EEG(OperateSubsidy):
    def __init__(self, name=None, apply_for=None, sbj_name=None,
                 dependent_vars=None):
        super().__init__(level='country', name=name, apply_for=apply_for,
                         sbj_name=sbj_name, dependent_vars=dependent_vars)

        # check the EEG subsidy mode
        # if set(self.modes).issubset({'surplus feed-in + fixed compensation',
        #                              'surplus feed-in + direct marketing',
        #                              'full feed-in + direct marketing',
        #                              'full feed-in + fixed compensation'}):
        #     pass
        # else:
        #     raise ValueError('The mode of EEG subsidy is not defined.')

    def add_rules(self, user='basic', building='all'):
        super().add_rules(user, building)
        # add the rules for the subsidy
        # check the EEG subsidy mode
        if set(self.modes).issubset({'surplus feed-in + fixed compensation',
                                     'surplus feed-in + direct marketing',
                                     'full feed-in + direct marketing',
                                     'full feed-in + fixed compensation'}):
            pass
        else:
            raise ValueError('The mode of EEG subsidy is not defined.')

    def add_cons(self, model):
        super().add_cons(model)
        self._constraint_rule(model, self.sbj_name, self.require_name)

    def _constraint_rule(self, model, sbj_name, e_grid_name):
        # total_e_grid = model.find_component('input_elec_' + e_grid_name)
        pv_to_e_grid = model.find_component('elec_' + sbj_name + '_' +
                                            e_grid_name)
        total_pv = model.find_component('output_elec_' + sbj_name)
        sub_price = model.find_component('subsidy_price_' + self.name + '_' +
                                         sbj_name)
        sub_annuity = model.find_component('sub_annuity_' + self.name + '_' +
                                           sbj_name)
        sub_quantity = model.find_component('sub_quantity_' + self.name + '_' +
                                            sbj_name)

        def pv_to_grid_rule(model, t):
            return pv_to_e_grid[t] == total_pv[t]

        for mode in self.modes:
            mode_rules = model.find_component('rule_' + self.name + '_' +
                                              sbj_name + '_' + mode)
            for index in range(len(self.rules[mode])):
                sub_rule = pyo.Constraint(expr=sub_annuity == sum(
                    sub_price * pv_to_e_grid[t] for t in model.time_step))
                mode_rules[index + 1].add_component('sub_rule_' + str(index),
                                                    sub_rule)

                sub_quantity_rule = pyo.Constraint(expr=sub_quantity == sum(
                    pv_to_e_grid[t] for t in model.time_step))
                mode_rules[index + 1].add_component('sub_quantity_rule_' +
                                                    str(index),
                                                    sub_quantity_rule)

                if mode in {'full feed-in + fixed compensation',
                            'full feed-in + direct marketing'}:
                    rule = pyo.Constraint(model.time_step,
                                          rule=pv_to_grid_rule)
                    mode_rules[index + 1].add_component('feed_in_' + str(index),
                                                        rule)
