from scripts.Component import Component


class HeatExchanger(Component):

    def __init__(self, comp_name, comp_type="HeatExchanger", comp_model=None):
        self.inputs = ['heat']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
