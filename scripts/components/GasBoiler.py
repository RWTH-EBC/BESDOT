from scripts.Component import Component


class GasBoiler(Component):
    def __init__(self, comp_name, comp_type="GasBoiler", comp_model=None):
        self.inputs = ['gas']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
