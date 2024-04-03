from scripts.Component import Component
import os

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class HybridBoiler(Component):
    """Hybrid boiler component class, which could burn both gas and hydrogen."""
    def __init__(self, comp_name, comp_type="HybridBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['gas', 'hydrogen']
        self.outputs = ['heat']

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
        for output in self.outputs:
            output_energy = model.find_component('output_' + output + '_' +
                                                 self.name)
            input_energy = model.find_component('input_' + self.inputs[0] +
                                                '_' + self.name)
            input_energy_2 = model.find_component('input_' + self.inputs[1] +
                                                  '_' + self.name)
            for t in model.time_step:
                model.cons.add(output_energy[t] == (input_energy[t] +
                               input_energy_2[t]) * self.efficiency[output])