from scripts.Component import Component


class GasGrid(Component):

    def __init__(self, comp_name, comp_type="GasGrid", comp_model=None):
        self.outputs = ['gas']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)

    def _constraint_conver(self, model):
        """
        The Grid has "no" fixed input and therefore it should not be constrainted
        """
        pass
