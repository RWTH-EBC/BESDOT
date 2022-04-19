import pyomo.environ as pyo
from scripts.Component import Component


class ElectricityMeter(Component):

    def __init__(self, comp_name, comp_type="ElectricityMeter", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['elec']
        self.outputs = ['elec']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def add_cons(self, model):
        self._constraint_conver(model)

    def add_vars(self, model):
        if 'elec' in self.energy_flows['input'].keys():
            for energy_type in self.inputs:
                input_energy = pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                model.add_component('input_' + energy_type + '_' + self.name,
                                    input_energy)

        if 'elec' in self.energy_flows['output'].keys():
            for energy_type in self.outputs:
                output_energy = pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                model.add_component('output_' + energy_type + '_' + self.name,
                                    output_energy)
