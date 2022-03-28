import warnings
import pyomo.environ as pyo
from scripts.components.HeatExchangerFluid import HeatExchangerFluid


class ThreePortValve(HeatExchangerFluid):
    """
    todo add description
    """
    def __init__(self, comp_name, comp_type="ThreePortValve"):
        # self.name = comp_name
        # self.component_type = comp_type
        # self.efficiency = {'heat': 1}
        #
        self.inputs = ['heat']
        self.outputs = ['heat']
        #
        # self.heat_flows_in = []
        # self.heat_flows_out = []

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type)

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
        flow_in_mass = False
        flow_in_temp = False
        flow_out_mass = False
        flow_out_temp = False

        for energy_flow_in in self.energy_flows['input']['heat']:
            if energy_flow_in in self.heat_flows_in:
                flow_in_mass = model.find_component(energy_flow_in[0] + '_' +
                                                    energy_flow_in[1] + '_mass')
                flow_in_temp = model.find_component(energy_flow_in[1] + '_' +
                                                    energy_flow_in[0] + '_temp')
        for energy_flow_out in self.energy_flows['output']['heat']:
            if energy_flow_out in self.heat_flows_out:
                flow_out_mass = model.find_component(energy_flow_out[0] + '_' +
                                                     energy_flow_out[
                                                         1] + '_mass')
                flow_out_temp = model.find_component(energy_flow_out[1] + '_' +
                                                     energy_flow_out[
                                                         0] + '_temp')

        if flow_in_mass and flow_in_temp and flow_out_mass and flow_out_temp:
            for t in model.time_step:
                model.cons.add(flow_in_mass[t] <= flow_out_mass[t])
                model.cons.add(flow_in_temp[t] == flow_out_temp[t])
        else:
            warnings.warn("Can't find heat flows in " + self.name)

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
