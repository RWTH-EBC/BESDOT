from scripts.Component import Component


class ElectricalConsumption(Component):

    def __init__(self, comp_name):
        super().__init__(comp_name=comp_name)

    def _read_properties(self, properties):
        """
        The component electrical consumption is a virtual component which links the
        inflexible electrical demand of the prosumer to the energy supply system.
        Therefore the component has an efficiency of 1. The
        """
        if not hasattr(self, 'efficiency'):
            self.efficiency = 1

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

    def add_variables(self, input_profiles, plant_parameters, var_dict, flows, model, T):
        """
        The consumption has no power constraints or doesn't cause costs
        """
        self._add_linking_variables(var_dict, flows, model, T)
        output_flow = (self.name, 'elec_dmd')  # Define output flow
        flows['electricity'][self.name][1].append(output_flow)  # Add output flow
        var_dict[output_flow] = input_profiles['elec_demand']  # Assign values to output flow in the var_dict
