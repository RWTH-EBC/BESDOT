import warnings
import pyomo.environ as pyo
from scripts.components.HeatExchangerFluid import HeatExchangerFluid


class ThreePortValve(HeatExchangerFluid):
    """
    todo add description
    """
    def __init__(self, comp_name, comp_type="ThreePortValve"):
        self.name = comp_name
        self.component_type = comp_type
        self.efficiency = {'heat': 1}

        self.inputs = ['heat']
        self.outputs = ['heat']

        self.heat_flows_in = []
        self.heat_flows_out = []

        if len(self.heat_flows_in) > 1:
            warnings.warn('more than one energy flow input is given for the '
                          'heat exchanger')
        if len(self.heat_flows_out) > 1:
            warnings.warn('more than one energy flow output is given for the '
                          'heat exchanger')

    def _constraint_mix(self, model):
        """After flow mixing in three port valve, flow in output side should be
         larger than the flow in input side. On the other hand, the temperature
         of fluid before and after division remain unchanged."""
        heat_input = self.heat_flows_in[0]
        mass_flow_in = model.find_component(heat_input[0] + '_' +
                                            heat_input[1] + '_mass')
        heat_output = self.heat_flows_out[0]
        mass_flow_out = model.find_component(heat_output[1] + '_' +
                                             heat_output[0] + '_mass')
        # Temperature of fluid before and after division
        temp_flow_in = model.find_component(heat_input[1] + '_' +
                                            heat_input[0] + '_temp')
        temp_flow_out = model.find_component(heat_output[1] + '_' +
                                             heat_output[0] + '_temp')

        for t in model.time_step:
            model.cons.add(mass_flow_in[t] <= mass_flow_out[t])
            model.cons.add(temp_flow_in[t] == temp_flow_out[t])

    def add_cons(self, model):
        self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        self._constraint_conver(model)
        self._constraint_mix(model)

    def add_vars(self, model):
        input_energy = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('input_heat_' + self.name, input_energy)

        output_energy = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('output_heat_' + self.name, output_energy)
