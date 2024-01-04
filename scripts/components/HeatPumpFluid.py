import pyomo.environ as pyo
from scripts.Component import Component
from scripts.FluidComponent import FluidComponent
from scripts.components import HeatPump
from pyomo.gdp import Disjunct, Disjunction


class HeatPumpFluid(HeatPump, FluidComponent):

    def __init__(self, comp_name, temp_profile, comp_type="HeatPumpFluid",
                 comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        # Define inputs and outputs before the initialisation of component,
        # otherwise we can't read properties properly. By getting efficiency,
        # the energy typ is needed.

        super().__init__(comp_name=comp_name,
                         temp_profile=temp_profile,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_temp(self, model):
        for heat_output in self.heat_flows_out:
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] + '_' + 'temp')
        for t in model.time_step:
            model.cons.add(t_out[t] <= 55)

    def _constraint_temp_gdp(self, model):
        outlet_temp = model.find_component('outlet_temp_' + self.name)
        size = model.find_component('size_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] + '_' + self.name)
        for heat_output in self.heat_flows_out:
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] + '_' + 'temp')

        for t in range(1, len(model.time_step)):
            u = Disjunct()
            #https: // www.energie - experten.org / heizung / waermepumpe / leistung / vorlauftemperatur
            c_1 = pyo.Constraint(expr=outlet_temp[t] <= 55)
            model.add_component('u_dis_' + str(t), u)
            u.add_component('u_1' + str(t), c_1)

            v = Disjunct()
            c_3 = pyo.Constraint(expr=output_energy[t] == 0)
            model.add_component('v_dis_' + str(t), v)
            v.add_component('v_1' + str(t), c_3)

            dj4 = Disjunction(expr=[u, v])
            model.add_component('dj4_dis_' + str(t), dj4)


    def add_cons(self, model):
        self._constraint_heat_outputs(model)
        self._constraint_maxpower(model)
        self._constraint_vdi2067(model)
        self._constraint_conver(model)
        #self._constraint_temp(model)
        self._constraint_temp_gdp(model)
