import warnings
import pyomo.environ as pyo
from scripts.Component import Component
from scripts.FluidComponent import FluidComponent
from scripts.components import HeatExchanger


class HeatExchangerFluid_Solar(HeatExchanger, FluidComponent):

    def __init__(self, comp_name, comp_type="HeatExchangerFluid_Solar",
                 comp_model=None, min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        # Default for energy conversion in heat exchanger
        self.efficiency['heat'] = 1

    def _constraint_temp(self, model):
        # Temperatur des Solarspeichers
        temp = model.find_component('temp_' + self.name)
        for energy_flow_in in self.energy_flows['input']['heat']:
            if energy_flow_in in self.heat_flows_in:
                in_flow_in_temp = model.find_component(energy_flow_in[1] + '_' +
                                                    energy_flow_in[0] + '_temp')
                in_flow_out_temp = model.find_component(energy_flow_in[0] +
                                                        '_' +
                                                    energy_flow_in[1] + '_temp')
        for energy_flow_out in self.energy_flows['output']['heat']:
            if energy_flow_out in self.heat_flows_out:
                out_flow_in_temp = model.find_component(energy_flow_out[1] +
                                                        '_' +
                                                        energy_flow_out[
                                                            0] + '_temp')
        for t in model.time_step:
            model.cons.add(in_flow_in_temp[t] == temp[t])
            #model.cons.add(in_flow_out_temp[t] >= temp[t])
            model.cons.add(out_flow_in_temp[t] == temp[t])

    def add_cons(self, model):
        self._constraint_temp(model)
        self._constraint_conver(model)

    def add_vars(self, model):
        input_energy = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('input_heat_' + self.name, input_energy)

        output_energy = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('output_heat_' + self.name, output_energy)

        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)