import pyomo.environ as pyo
from scripts.Component import Component
from scripts.FluidComponent import FluidComponent
from scripts.components import HeatPump
from scripts.components.HeatPumpQli import HeatPumpQli
import warnings

class HeatPumpFluidQli(HeatPumpQli, FluidComponent):

    def __init__(self, comp_name, temp_profile, comp_type="HeatPumpFluidQli",
                 comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        # Define inputs and outputs before the initialisation of component,
        # otherwise we can't read properties properly. By getting efficiency,
        # the energy typ is needed.

        super().__init__(comp_name=comp_name, temp_profile=temp_profile,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)



    def _constraint_temp(self, model):
        for heat_output in self.heat_flows_out:
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in model.time_step:
                model.cons.add(t_out[t] == self.outlet_temp)

    def add_cons(self, model):
        super().add_cons(model)
        self._constraint_temp(model)
        self._constraint_heat_outputs(model)
