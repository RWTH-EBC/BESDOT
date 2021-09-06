from component_library.component_models.BaseComponent \
    import BaseComponent


class HotWaterConsumption(BaseComponent):

    def __init__(self, comp_name, min_size, max_size, current_size, properties):
        super().__init__(comp_name=comp_name,
                         commodity_1="heat",
                         commodity_2="heat",
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         comp_type="HotWaterConsumption",
                         properties=properties)

    def _read_properties(self, properties):
        """
        The component hot water consumption is a virtual component which links the
        inflexible electrical demand of the prosumer to the energy supply system.
        Therefore the component has an efficiency of 1. The
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

    def add_variables(self, input_profiles, plant_parameters, var_dict, flows,
                      model, T):
        # todo: change therm to heat
        # todo: consider "heat_demand" as a new constraint
        self._add_linking_variables(var_dict, flows, model, T)
        output_flow = (self.name, 'hot_water_dmd')  # Define output flow
        flows['heat'][self.name][1].append(output_flow)  # Add output flow

        var_dict[output_flow] = input_profiles['hot_water_demand']  # Assign
        # values to output flow in the var_dict
