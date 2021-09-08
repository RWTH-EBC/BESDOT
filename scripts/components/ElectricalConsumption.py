from scripts.Component import Component


class ElectricalConsumption(Component):

    def __init__(self, comp_name, consum_profile,
                 comp_type="ElectricalConsumption", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['elec']
        self.consum_profile = consum_profile

    def _constraint_vdi2067(self, model, var_dict, T):
        """
        The electrical consumption has currently no max. power or investment
        constraint. However, in the future this can used to implement costs
        of electric energy consumers.
        """
        pass

    def _constraint_maxpower(self, model, flows, var_dict, T):
        """
        The electrical consumption has currently no max. power or investment
        constraint. However, in the future this can be used to implement the
        max. power of single power socket etc.
        """
        pass
