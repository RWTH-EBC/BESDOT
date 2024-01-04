from scripts.components.Storage import Storage
# import pyomo.environ as pyo
# from pyomo.gdp import Disjunct, Disjunction
# from utils.calc_annuity_vdi2067 import calc_annuity

small_num = 0.0001


class Battery(Storage):

    def __init__(self, comp_name, comp_type="Battery", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['elec']
        self.outputs = ['elec']

        self.set_init = True

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
