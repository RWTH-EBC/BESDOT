import pyomo.environ as pyo
from scripts.Component import Component


class ElectricityGrid(Component):

    def __init__(self, comp_name, comp_type="ElectricityGrid", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['elec']
        self.outputs = ['elec']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_conver(self, model):
        """
        The Grid has "no" fixed input and therefore it should not be constrainted
        """
        pass

    def add_vars(self, model):
        """Rewrite the function in case of input and output """
        comp_size = pyo.Var(bounds=(self.min_size, self.max_size))
        model.add_component('size_' + self.name, comp_size)

        annual_cost = pyo.Var(bounds=(0, None))
        model.add_component('annual_cost_' + self.name, annual_cost)

        invest = pyo.Var(bounds=(0, None))
        model.add_component('invest_' + self.name, invest)

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
