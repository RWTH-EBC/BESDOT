import numpy as np
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy


small_num = 0.0001


class PurchaseSubsidy(Subsidy):
    def __init__(self, level, name=None, apply_for=None, sbj_name=None,
                 dependent_vars=None):
        super().__init__(level=level, sub_type='purchase', name=name,
                         apply_for=apply_for, sbj_name=sbj_name,
                         dependent_vars=dependent_vars)

    # def add_vars(self, model):
    #     super().add_vars(model)
    #     # The subsidy for PV in EEG is for generated energy, so the subsidies
    #     # is added to each time step.
    #     total_subsidy = pyo.Var(bounds=(0, None))
    #     model.add_component('total_subsidy_' + self.name, total_subsidy)

    def add_cons(self, model):
        """add the constraints of the subsidy. sub_name is the name of the
        subject to which the subsidy is applied."""
        self._constraint_rule(model)

    def _constraint_rule(self, model):
        subsidy = model.find_component('subsidy_' + self.name + '_' +
                                       self.sbj_name)

        if self.dependent_vars == 'investment':
            depend_var = model.find_component('invest_' + self.sbj_name)
        elif self.dependent_vars == 'size':
            depend_var = model.find_component('size_' + self.sbj_name)
        elif self.dependent_vars == 'area':
            depend_var = model.find_component('solar_area_' + self.sbj_name)
        else:
            raise ValueError('The dependent variable of subsidy {} is not '
                             'defined.'.format(self.name))

        if 'no_mode' in self.rules:
            rules = self.rules['no_mode']
        else:
            raise ValueError('The rules of subsidy {} is not defined.'
                             .format(self.name))

        rule_nr = len(rules)
        rule = Disjunct(pyo.RangeSet(rule_nr + 1))
        model.add_component('rule_' + self.name + '_' + self.sbj_name, rule)
        rule_list = []
        for index in range(len(rules)):
            if rules[index]['lower'] == 0:
                bound_low = pyo.Constraint(expr=depend_var >= rules[index][
                    'lower'] + small_num)
            else:
                bound_low = pyo.Constraint(expr=depend_var >= rules[index][
                    'lower'])

            if rules[index]['upper'] == 'inf':
                bound_up = pyo.Constraint(expr=depend_var <= np.inf)
            else:
                bound_up = pyo.Constraint(expr=depend_var <= rules[index][
                    'upper'] - small_num)

            sub_rule = pyo.Constraint(expr=rules[index]['coefficient'] *
                                       depend_var + rules[index][
                                       'constant'] == subsidy)

            # the name for constraints in disjunct should be different? need
            # to be checked later
            rule[index + 1].add_component(self.name + '_bound_low_' + str(
                index + 1), bound_low)
            rule[index + 1].add_component(self.name + '_bound_up_' + str(
                index + 1), bound_up)
            rule[index + 1].add_component(self.name + '_rule_' + str(index + 1),
                                          sub_rule)
            rule_list.append(rule[index + 1])

        # if the dependent variable is zero, the subsidy is zero
        sub_rule = pyo.Constraint(expr=subsidy == 0)
        bound = pyo.Constraint(expr=depend_var == 0)
        rule[rule_nr + 1].add_component(self.name + '_rule_0', sub_rule)
        rule[rule_nr + 1].add_component(self.name + '_bound_0', bound)
        rule_list.append(rule[rule_nr + 1])

        disjunction = Disjunction(expr=rule_list)
        model.add_component('disjunction_' + self.name + '_' + self.sbj_name,
                            disjunction)
