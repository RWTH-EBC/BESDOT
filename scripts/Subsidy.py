import pyomo.environ as pyo
from utils.get_subsidy import find_sub_rules
from utils.calc_annuity_vdi2067 import calc_annuity


class Subsidy(object):
    """
    The subsidies for each energy device in building.
    ------------------------------------------------
    enact_year: the year, in which the regulation was enacted.
    version: In case some regulation have multiple version in a year,
     a secondary attribute 'version' is added. default set None
    components: the list of all subsidized device class.
    type: the type could be set as 'purchase' or 'operate'
    """
    def __init__(self, level, sub_type, name=None, apply_for=None,
                 sbj_name=None, dependent_vars=None):
        """apply_for: could be building or specific components."""
        self.name = name
        self.level = level
        self.sub_type = sub_type
        self.apply_for = apply_for
        self.sbj_name = sbj_name
        self.dependent_vars = dependent_vars
        self.rules = {}

    def add_rules(self, user='basic', building='all'):
        self.rules['no_mode'] = find_sub_rules(self.name, self.sub_type,
                                               self.apply_for, user,
                                               building, self.dependent_vars)

    def add_vars(self, model):
        # The subsidy for PV in EEG is for generated energy, so the subsidies
        # is added to each time step.
        subsidy = pyo.Var(bounds=(0, 10e8))
        model.add_component('subsidy_' + self.name + '_' + self.sbj_name,
                            subsidy)

        sub_annuity = pyo.Var(bounds=(0, 10e8))
        model.add_component('sub_annuity_' + self.name + '_' + self.sbj_name,
                            sub_annuity)
