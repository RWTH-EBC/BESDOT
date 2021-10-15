from scripts.Component import Component


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

    def _constraint_maxpower(self, model):
        output_powers = model.find_component('output_' +
                                             self.outputs[0] + '_' +
                                             self.name)
        size = model.find_component('size_' + self.name)

        for t in model.time_step:
            model.cons.add(output_powers[t] == size)
