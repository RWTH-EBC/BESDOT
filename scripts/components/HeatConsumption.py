from scripts.Component import Component


class HeatConsumption(Component):

    def __init__(self, comp_name, consum_profile,
                 comp_type="HeatConsumption", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['gas']
        self.consum_profile = consum_profile

    def _read_properties(self, properties):
        """
        The component heat consumption is a virtual component which links the
        inflexible electrical demand of the prosumer to the energy supply system.
        Therefore the component has an efficiency of 1. The
        """
        if not hasattr(self, 'efficiency'):
            self.efficiency = 1

    def _constraint_vdi2067(self, model, var_dict, T):
        """
        The heat consumption has currently no max. power or investment
        constraint.
        """
        pass

    def _constraint_maxpower(self, model, flows, var_dict, T):
        """
        The heat consumption has currently no max. power or investment
        constraint.
        """
        pass

    # def add_variables(self, input_profiles, plant_parameters, var_dict, flows,
    #                   model, T):
    #
    #     output_flow = (self.name, 'therm_dmd')  # Define output flow
    #     flows['heat'][self.name][1].append(output_flow)  # Add output flow
    #
    #     var_dict[output_flow] = input_profiles['therm_demand']
