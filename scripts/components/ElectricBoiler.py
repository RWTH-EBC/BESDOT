from scripts.Component import Component


class ElectricBoiler(Component):

    def __init__(self, comp_name, comp_type="ElectricBoiler", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['elec']
        self.outputs = ['heat']
