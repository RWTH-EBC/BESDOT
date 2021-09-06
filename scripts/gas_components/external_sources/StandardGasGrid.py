from component_library.component_models.BaseComponent import BaseComponent


class StandardGasGrid(BaseComponent):

    def __init__(self, comp_name, min_size, max_size, current_size, properties, comp_type='Gas_Grid'):
        super().__init__(comp_name=comp_name,
                         commodity_1='gas',
                         commodity_2='gas',
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         comp_type=comp_type,
                         properties=properties)

    def _constraint_conser(self, model, flows, var_dict, T):
        """
        The Grid has "no" fixed input and therefore it should not be constrainted
        """
        pass
