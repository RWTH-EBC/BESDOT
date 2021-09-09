from scripts.Component import Component


class CHP(Component):

    def __init__(self, comp_name, comp_type="CHP", comp_model=None):
        self.inputs = ['gas']
        self.outputs = ['heat', 'elec']
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
