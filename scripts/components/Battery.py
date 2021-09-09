from scripts.components.Storage import Storage


class Battery(Storage):

    def __init__(self, comp_name, comp_type="Battery", comp_model=None):
        self.inputs = ['elec']
        self.outputs = ['elec']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
