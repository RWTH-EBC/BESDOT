import os
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Component import Component

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

small_num = 0.0001


class BiomassBoiler(Component):
    def __init__(self, comp_name, comp_type="BiomassBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['biomass']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.min_part_load = 0.25

    def add_cons(self, model):
        """The minimum part-load ratio is set for biomass boiler."""
        super().add_cons(model)
        self._constraint_part_load(model)
