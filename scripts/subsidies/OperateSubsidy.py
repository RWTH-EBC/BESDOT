import numpy as np
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction

from scripts.Subsidy import Subsidy
from utils.get_subsidy import find_sub_rules
from utils.get_subsidy import find_sub_modes
from utils.get_subsidy import find_mode_rules
from utils.get_subsidy import find_rules_from_df

small_num = 0.0001


class OperateSubsidy(Subsidy):
    def __init__(self, level, name=None, apply_for=None, sbj_name=None,
                 dependent_vars=None):
        super().__init__(level=level, sub_type='operate', name=name,
                         apply_for=apply_for, sbj_name=sbj_name,
                         dependent_vars=dependent_vars)
        self.modes = None
        self.require_name = None

    def add_rules(self, user='basic', building='all'):
        self.modes = find_sub_modes(self.name, 'operate',
                                    self.apply_for, user, building)
        for mode in self.modes:
            self.rules[mode] = find_mode_rules(self.name, 'operate',
                                               self.apply_for, mode, user,
                                               building, self.dependent_vars)

    def add_require(self, require_name):
        """add the component name, which should get the produced energy.
        in most situation the required component is the electricity grid."""
        self.require_name = require_name

    def add_vars(self, model):
        super().add_vars(model)
        # The subsidy EEG or KWKG is for generated energy, so the subsidies
        # is calculated with subsidy price for generated energy.
        # This subsidy price for generated energy is also determined by the
        # size of the energy device, which makes the price a variable. And
        # the total subsidy is the product of the subsidy price and the
        # energy amount, so that the model would be a non-linear model. Using
        # gurobi as the solver, the model might able be solved, as it could
        # solve the quadratic model.
        sub_price = pyo.Var(bounds=(0, 100))
        model.add_component('subsidy_price_' + self.name + '_' + self.sbj_name,
                            sub_price)

        sub_quantity = pyo.Var(bounds=(0, 10e8))
        model.add_component('sub_quantity_' + self.name + '_' + self.sbj_name,
                            sub_quantity)

    def add_cons(self, model):
        """add the constraints of the subsidy. sub_name is the name of the
        subject to which the subsidy is applied."""
        self._constraint_price(model, self.sbj_name)

    def _constraint_price(self, model, sbj_name):
        # The subsidy EEG or KWKG is for generated energy, so the subsidies
        # price should be calculated with size.
        # Should attention that the subsidy price is the weighted average of
        # different tariffs, but not the tariff of size of the energy device.
        # An example is, the 76 kW device with the following tariffs:
        #   0-30 kW: 0.12
        #   30-50 kW: 0.11
        #   50-100 kW: 0.1
        # the calculated subsidy price is 0.12 * (30 - 0) / 76 + 0.11 * (50 -
        # 30) / 76 + 0.1 * (76 - 50) / 76 = 0.111, but not 0.1.
        sub_price = model.find_component('subsidy_price_' + self.name + '_' +
                                         sbj_name)
        depend_var = model.find_component('size_' + sbj_name)

        mode_list = []
        for mode in self.modes:
            rules = self.rules[mode]
            rule_nr = len(rules)
            rule = Disjunct(pyo.RangeSet(rule_nr + 1))
            model.add_component('rule_' + self.name + '_' + sbj_name + '_' +
                                mode, rule)
            # rule_list = []
            weighted_price_expr = 0
            for index in range(len(rules)):
                bound_low = pyo.Constraint(expr=depend_var >= rules[index][
                    'lower'])

                if rules[index]['upper'] == 'inf':
                    bound_up = pyo.Constraint(expr=depend_var <= np.inf)
                else:
                    bound_up = pyo.Constraint(expr=depend_var <= rules[index][
                        'upper'] - small_num)

                # The calculated subsidy price is the weighted average of
                # relevant tariffs.
                price_rule = pyo.Constraint(expr=sub_price * depend_var ==
                     rules[index]['coefficient'] * (depend_var - rules[
                     index]['lower']) + weighted_price_expr)

                rule[index + 1].add_component(self.name + '_bound_low_' + str(
                    index + 1), bound_low)
                rule[index + 1].add_component(self.name + '_bound_up_' + str(
                    index + 1), bound_up)
                rule[index + 1].add_component(self.name + '_' + mode
                                              + '_rule_' + str(index + 1),
                                              price_rule)
                mode_list.append(rule[index + 1])

                lower_bound = rules[index]['lower']
                upper_bound = 10e5 if rules[index]['upper'] == 'inf' else (
                    rules)[index]['upper']
                range_size = upper_bound - lower_bound
                weighted_price_expr += rules[index]['coefficient'] * range_size

            # disjunction = Disjunction(expr=rule_list)
            # model.add_component('disjunction_' + self.name + '_' + mode + '_'
            #                     + sbj_name, disjunction)
            # disj = model.find_component('disjunction_' + self.name + '_' + mode
            #                             + '_' + sbj_name)
            # mode_list.append(disj)

        disjunction = Disjunction(expr=mode_list)
        model.add_component('disjunction_' + self.name + '_' + sbj_name,
                            disjunction)
