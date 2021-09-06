from component_library.component_models.BaseComponent \
    import BaseComponent


class Radiator(BaseComponent):

    def __init__(self, comp_name, min_size, max_size, current_size, properties):
        # todo: commodity_2 should change to 'heat_demand'
        super().__init__(comp_name=comp_name,
                         commodity_1="heat",
                         commodity_2="heat",
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         comp_type="Radiator",
                         properties=properties)

    def add_all_constr(self, model, flows, var_dict, T):
        # For heat consumption there should only one constrain, that the sum
        # of heat consumption device equal to heat demand
        super()._constraint_conser(model, flows, var_dict, T)

    def add_variables(self, input_parameters, plant_parameters, var_dict, flows,
                      *args):
        # todo: change therm to heat
        # todo: consider "heat_demand" as a new constraint
        output_flow = (self.name, 'therm_dmd')  # Define output flow
        flows['heat'][self.name][1].append(output_flow)  # Add output flow

        var_dict[output_flow] = input_parameters['therm_demand']  # Assign
        # values to output flow in the var_dict
