import os
import warnings

import pandas as pd
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.CHP import CHP

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))


class CHPFluidSmall(CHP, FluidComponent):

    def __init__(self, comp_name, comp_type="CHPFluidSmall", comp_model=None,
                 min_size=2, max_size=50, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.outlet_temp = None

    # Pel = elektrische Nennleistung = comp_size
    # Qth = thermische Nennleistung
    def _constraint_Pel(self, model):
        Pel = model.find_component('size_' + self.name)
        Qth = model.find_component('therm_size_' + self.name)
        model.cons.add(Qth == 2.1178 * Pel + 2.5991)

    def _constraint_therm_eff(self, model):
        Qth = model.find_component('therm_size_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        for t in model.time_step:
            model.cons.add(therm_eff[t] == 0.705 - 0.0008 * (Qth - 44) -
                           0.006 * (inlet_temp[t] - 30))

    def _constraint_elec_eff(self, model):
        Pel = model.find_component('size_' + self.name)
        elec_eff = model.find_component('elec_eff_' + self.name)
        model.cons.add(elec_eff == (0.1016 * Pel + 29.609) / 100)

    def _constraint_temp(self, model):

        chp_properties_path = os.path.join(base_path, "data",
                                                  "component_database",
                                                  "CHPFluidSmall",
                                                  "CHPFluidSmall1.csv")
        chp_properties = pd.read_csv(chp_properties_path)
        if 'outlet_temp' in chp_properties.columns:
            self.outlet_temp = float(chp_properties['outlet_temp'])
        else:
            warnings.warn(
                "In the model database for " + self.component_type +
                " lack of column for outlet temperature.")

        outlet_temp = model.find_component('outlet_temp_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
        for t in model.time_step:
            model.cons.add(outlet_temp[t] == t_out[t])
            model.cons.add(inlet_temp[t] == t_in[t])
            model.cons.add(outlet_temp[t] == self.outlet_temp)


    def _constraint_conver(self, model):
        Pel = model.find_component('size_' + self.name)
        Qth = model.find_component('therm_size_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        #elec_eff = model.find_component('elec_eff_' + self.name)
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_heat = model.find_component(
            'output_' + self.outputs[0] + '_' + self.name)
        output_elec = model.find_component(
            'output_' + self.outputs[1] + '_' + self.name)
        status = model.find_component('status_' + self.name)

        for t in model.time_step:
            model.cons.add(input_energy[t] * therm_eff[t] == output_heat[t])
            #model.cons.add(input_energy[t] * elec_eff == output_elec[t])
            model.cons.add(Qth * status[t] == output_heat[t])
            model.cons.add(Pel * status[t] == output_elec[t])

    def add_cons(self, model):
        self._constraint_Pel(model)
        self._constraint_therm_eff(model)
        #self._constraint_elec_eff(model)
        self._constraint_temp(model)
        self._constraint_conver(model)
        self._constraint_heat_outputs(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)

        Qth = pyo.Var(bounds=(0, None))
        model.add_component('therm_size_' + self.name, Qth)

        therm_eff = pyo.Var(model.time_step, bounds=(0, 1))
        model.add_component('therm_eff_' + self.name, therm_eff)

        #elec_eff = pyo.Var(bounds=(0, 1))
        #model.add_component('elec_eff_' + self.name, elec_eff)

        outlet_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('outlet_temp_' + self.name, outlet_temp)

        inlet_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('inlet_temp_' + self.name, inlet_temp)

        status = pyo.Var(model.time_step, domain=pyo.Binary)
        model.add_component('status_' + self.name, status)
