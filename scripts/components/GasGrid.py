from scripts.Component import Component


class GasGrid(Component):

    def __init__(self, comp_name, comp_type="GasGrid", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.outputs = ['gas']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_conver(self, model):
        pass

    # todo (qli): building.py Zeile 342 anpassen
    def _constraint_gas_balance(self, model):
        output_gas = model.find_component('output_gas_' + self.name)
        # todo (qli): Name anpassen (self.name + '_chp_big')
        energy_flow_gas = model.find_component(self.name + '_chp_small')
        for t in model.time_step:
            model.cons.add(output_gas[t] == energy_flow_gas[t])

    # todo (qli): building.py Zeile 342 anpassen
    def add_cons(self, model):
        self._constraint_gas_balance(model)
