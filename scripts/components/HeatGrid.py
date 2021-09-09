from scripts.Component import Component


class HeatGrid(Component):

    def __init__(self, comp_name, comp_type="HeatGrid", comp_model=None):
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)

    def _constraint_conver(self, model):
        """
        The Grid has "no" fixed input and therefore it should not be constrainted
        """
        pass
