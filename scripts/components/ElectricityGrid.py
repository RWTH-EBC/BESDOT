import pyomo.environ as pyo
from scripts.Component import Component


class ElectricityGrid(Component):

    def __init__(self, comp_name, comp_type="ElectricityGrid", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.outputs = ['elec']

    def _constraint_conser(self, model, flows, var_dict, T):
        """
        The Grid has "no" fixed input and therefore it should not be constrainted
        """
        pass

    def add_vars(self, model):
        """There isn't inputs and investigation for grid"""
        output_energy = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('output_energy_' + self.name, output_energy)
