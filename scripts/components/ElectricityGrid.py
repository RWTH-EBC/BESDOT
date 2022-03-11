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

    # todo (qli): building.py Zeile 342 anpassen
    def _constraint_elec_balance(self, model):
        sell_elec = model.find_component('input_elec_' + self.name)
        # todo (qli): Name anpassen ('chp_big_' + self.name + '_elec')
        energy_flow_elec = model.find_component('chp_small_' + self.name + '_elec')
        for t in model.time_step:
            model.cons.add(sell_elec[t] == energy_flow_elec[t])

    # todo (qli): building.py Zeile 342 anpassen
    def add_cons(self, model):
        self._constraint_elec_balance(model)
