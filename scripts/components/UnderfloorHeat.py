from scripts.Component import Component


class UnderfloorHeat(Component):
    """
    pass
    """
    def __init__(self, comp_name, comp_type="UnderfloorHeat", comp_model=None):
        self.inputs = ['heat']
        self.outputs = ['heat']  # todo: same as Radiator

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
