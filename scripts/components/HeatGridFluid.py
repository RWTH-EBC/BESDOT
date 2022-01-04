import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.HeatGrid import HeatGrid


class HeatGridFluid(FluidComponent, HeatGrid):
    def __init__(self, comp_name, comp_type="HeatGridFluid",
                 comp_model=None, min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_temp(self, model, temp=80):
        """The supply temperature of heat grid is set to a constant value"""
        heat_output = self.heat_flows_out[0]
        t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                     '_' + 'temp')
        for t in range(len(model.time_step)):
            model.cons.add(t_out[t + 1] == temp)

    def add_cons(self, model):
        self._constraint_heat_outputs(model)
        self._constraint_mass_flow(model)
        self._constraint_temp(model)
        self._constraint_maxpower(model)
        self._constraint_vdi2067(model)
