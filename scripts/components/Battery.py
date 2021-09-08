import pyomo.environ as pyo
from scripts.Storage import Storage
import warnings


class Battery(Storage):

    def __init__(self, comp_name, comp_type="Battery", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['elec']
        self.outputs = ['elec']
