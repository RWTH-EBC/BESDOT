from scripts.Component import Component


class Radiator(Component):

    def __init__(self, comp_name, comp_type="Radiator", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['heat']
        self.outputs = ['heat']  # todo: maybe new outputs with demand

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def add_cons(self, model):
        # For heat consumption there should only one constrain, that the sum
        # of heat consumption device equal to heat demand
        super()._constraint_conver(model)

    # def add_variables(self, input_parameters, plant_parameters, var_dict, flows,
    #                   *args):
    #     # todo: consider "heat_demand" as a new constraint
    #     output_flow = (self.name, 'therm_dmd')  # Define output flow
    #     flows['heat'][self.name][1].append(output_flow)  # Add output flow
    #
    #     var_dict[output_flow] = input_parameters['therm_demand']  # Assign
    #     # values to output flow in the var_dict
