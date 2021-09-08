from scripts.Component import Component


class HotWaterConsumption(Component):

    def __init__(self, comp_name, consum_profile,
                 comp_type="HotWaterConsumption", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['heat']
        self.consum_profile = consum_profile

    def _read_properties(self, properties):
        """
        The component hot water consumption is a virtual component
        """
        if not hasattr(self, 'efficiency'):
            self.efficiency = 1

    def _constraint_vdi2067(self, model, var_dict, T):
        """
        The hot water consumption has currently no max. power or investment
        constraint. However, in the future this can used to implement costs
        of electric energy consumers.
        """
        pass

    def _constraint_maxpower(self, model, flows, var_dict, T):
        """
        The hot water consumption has currently no max. power or investment
        constraint. However, in the future this can be used to implement the
        max. power of single power socket etc.
        """
        pass

    # def add_variables(self, input_profiles, plant_parameters, var_dict, flows,
    #                   model, T):
    #     # todo: change therm to heat
    #     # todo: consider "heat_demand" as a new constraint
    #     self._add_linking_variables(var_dict, flows, model, T)
    #     output_flow = (self.name, 'hot_water_dmd')  # Define output flow
    #     flows['heat'][self.name][1].append(output_flow)  # Add output flow
    #
    #     var_dict[output_flow] = input_profiles['hot_water_demand']  # Assign
    #     # values to output flow in the var_dict
