from scripts.Component import Component


class GasHeatPump(Component):

    def __init__(self, comp_name, temp_profile, comp_type="GasHeatPump",
                 comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['gas']
        self.outputs = ['heat']
        self.temp_profile = temp_profile

        # todo: the cop of gas heat pump is set to constant. For further
        #  development could be change to variable value like the HeatPump
