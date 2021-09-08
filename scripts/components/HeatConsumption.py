from scripts.Component import Component


class HeatConsumption(Component):

    def __init__(self, comp_name):
        super().__init__(comp_name=comp_name)

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
        constraint. However, in the future this can used to implement costs
        of electric energy consumers.
        """
        pass

    def _constraint_maxpower(self, model, flows, var_dict, T):
        """
        The heat consumption has currently no max. power or investment
        constraint. However, in the future this can be used to implement the
        max. power of single power socket etc.
        """
        pass

    def add_variables(self, input_profiles, plant_parameters, var_dict, flows,
                      model, T):
        # todo: change therm to heat
        # todo: consider "heat_demand" as a new constraint
        self._add_linking_variables(var_dict, flows, model, T)
        output_flow = (self.name, 'therm_dmd')  # Define output flow
        flows['heat'][self.name][1].append(output_flow)  # Add output flow

        var_dict[output_flow] = input_profiles['therm_demand']  # Assign
        # values to output flow in the var_dict
