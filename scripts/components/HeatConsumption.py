from scripts.Component import Component


class HeatConsumption(Component):

    def __init__(self, comp_name, consum_profile,
                 comp_type="HeatConsumption", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.consum_profile = consum_profile

    def _read_properties(self, properties):
        """
        The component heat consumption is a virtual component which links the
        inflexible electrical demand of the prosumer to the energy supply system.
        Therefore the component has an efficiency of 1. The
        """
        if not hasattr(self, 'efficiency'):
            self.efficiency = 1

    def _constraint_vdi2067(self, model):
        """
        The heat consumption has currently no max. power or investment
        constraint.
        """
        pass

    def _constraint_maxpower(self, model):
        """
        The heat consumption has currently no max. power or investment
        constraint.
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

    # def add_variables(self, input_profiles, plant_parameters, var_dict, flows,
    #                   model, T):
    #
    #     output_flow = (self.name, 'therm_dmd')  # Define output flow
    #     flows['heat'][self.name][1].append(output_flow)  # Add output flow
    #
    #     var_dict[output_flow] = input_profiles['therm_demand']
