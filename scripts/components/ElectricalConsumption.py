from scripts.Component import Component


class ElectricalConsumption(Component):

    def __init__(self, comp_name, consum_profile,
                 comp_type="ElectricalConsumption", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['elec']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.consum_profile = consum_profile

    def _constraint_vdi2067(self, model):
        """
        The electrical consumption has currently no max. power or investment
        constraint. However, in the future this can used to implement costs
        of electric energy consumers.
        """
        pass

    def _constraint_maxpower(self, model):
        """
        The electrical consumption has currently no max. power or investment
        constraint. However, in the future this can be used to implement the
        max. power of single power socket etc.
        """
        pass

    def _constraint_conver(self, model):
        """The input energy for Consumption should equal to the demand profil"""
        input_energy = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        for t in model.time_step:
            ####################################################################
            # ATTENTION!!! The time_step in pyomo is from 1 to 8760 and
            # python list is from 0 to 8759, so the index should be modified.
            ####################################################################
            model.cons.add(input_energy[t] == self.consum_profile[t-1])
