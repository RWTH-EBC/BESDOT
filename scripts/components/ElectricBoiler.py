from scripts.Component import Component
# import pyomo.environ as pyo
# from pyomo.gdp import Disjunct, Disjunction
# from utils.calc_annuity_vdi2067 import calc_annuity

small_num = 0.0001


class ElectricBoiler(Component):

    def __init__(self, comp_name, comp_type="ElectricBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0, cost_model=0):
        self.inputs = ['elec']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         cost_model=cost_model)
