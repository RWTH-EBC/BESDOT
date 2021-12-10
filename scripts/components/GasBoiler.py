import warnings
import pyomo.environ as pyo
from scripts.Component import Component
import warnings
from tools.calc_exhaust_gas_loss import calc_exhaust_gas_loss
import os

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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






