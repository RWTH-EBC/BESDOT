"""
This code is inherited from the parent class HeatPump. It inherits
all properties and methods from the HeatPump class.
"""
import pyomo.environ as pyo
from scripts.components.HeatPump import HeatPump


class HeatPumpWasteHeat(HeatPump):
    def __init__(self, comp_name, comp_type="HeatPumpWasteHeat",
                 comp_model=None,
                 min_size=0, max_size=1000, current_size=0):

        super().__init__(comp_name=comp_name,
                         temp_profile=[],
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.inputs = ['elec', 'heat']
        self.sink_temp = 50
        self.source_temp = 16
        self.cop = ((self.sink_temp + 273.15) * self.efficiency[self.outputs[0]]
                    / (self.sink_temp - self.source_temp))

    def _constraint_conver(self, model):
        """
        Energy conservation equation for heat pump with variable COP value.
        Heat pump has only one input and one output, maybe? be caution for 5
        generation heat network.
        """
        # electricity
        input_powers = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        # waste heat, todo check if this is correct
        input_heat = model.find_component('input_' + self.inputs[1] + '_' +
                                            self.name)
        # heat supply
        output_heat = model.find_component('output_' + self.outputs[0] + '_' +
                                             self.name)
        for t in model.time_step:
            model.cons.add(output_heat[t] == input_powers[t] * self.cop)
            model.cons.add(output_heat[t] == input_powers[t] + input_heat[t])

    # def _constraint_waste_heat_limit(self, model):
    #     """
    #     Limit the waste heat to the maximum value.
    #     """
    #     # waste heat, todo check if this is correct
    #     input_heat = model.find_component('input_' + self.inputs[1] + '_' +
    #                                         self.name)
    #
    #     for t in model.time_step:
    #         model.cons.add(input_heat[t] <= self.max_size)

    def _constraint_cop(self, model):
        pass

    def add_cons(self, model):
        super().add_cons(model)