import os
import warnings

import pandas as pd
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.CHP import CHP

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))


# kleine BHKW (Pel <= 50kW) mit Brennwertnutzung
# Die Rücklauftemperatur der BHKW muss kleiner als 50 Grad sein,
# damit der Brennwert ausgenutzt werden kann.
# water_tes_temp (1) <= 50
class CHPFluidSmall(CHP, FluidComponent):
    # Die elektrische Nennleistung der BHKW mit Brennwertnutzung
    # sollte kleiner gleich 50 kW.
    def __init__(self, comp_name, comp_type="CHPFluidSmall", comp_model=None,
                 min_size=0, max_size=50, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.comp_type = comp_type
        self.comp_model = comp_model
        # todo (qli): start_price recherchieren
        self.start_price = 100

        # todo (qli): building.py Zeile 342 anpassen
        self.heat_flows_in = []
        self.heat_flows_out = []

   # todo (qli): building.py Zeile 342 anpassen
    def add_heat_flows(self, bld_heat_flows):
        for element in bld_heat_flows:
            if element[0] != 'e_grid' and element[1] != 'e_grid':
                if self.name == element[0]:
                    self.heat_flows_out.append(element)
                if self.name == element[1]:
                    self.heat_flows_in.append(element)

    # Pel = elektrische Nennleistung = comp_size
    # Qth = thermische Nennleistung
    # Qth = f(Pel)
    def _constraint_Pel(self, model):
        Pel = model.find_component('size_' + self.name)
        Qth = model.find_component('therm_size_' + self.name)
        model.cons.add(Qth == 2.1178 * Pel + 2.5991)

    # ηth = f(Qth, Tein)
    # Die Beziehung zwischen ηth und Taus wird vernachlässigt.
    def _constraint_therm_eff(self, model):
        Qth = model.find_component('therm_size_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        for t in model.time_step:
            model.cons.add(therm_eff[t] == 0.705 - 0.0008 * (Qth - 44) -
                           0.006 * (inlet_temp[t] - 30))

    # verbinden die Parameter der einzelnen Anlage mit den Parametern zwischen
    # zwei Anlagen (simp_matrix).
    # Die Rücklauftemperatur der BHKW muss kleiner als 50 Grad sein,
    # damit der Brennwert ausgenutzt werden kann.
    # Zu hohe Temperaturspreizng (>25 Grad) führt zur Beschädigung der Anlagen.
    def _constraint_temp(self, model):
        outlet_temp = model.find_component('outlet_temp_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        # Zu hohe Temperaturspreizng führt zur Beschädigung der Anlagen.
        for t in model.time_step:
            model.cons.add(outlet_temp[t] - inlet_temp[t] <= 25)
            model.cons.add(inlet_temp[t] <= 50)
        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in model.time_step:
                model.cons.add(outlet_temp[t] == t_out[t])
                model.cons.add(inlet_temp[t] == t_in[t])

    # status_chp ----- zur Beschreibung der taktenden Betrieb
    # input * η = output
    def _constraint_conver(self, model):
        Pel = model.find_component('size_' + self.name)
        Qth = model.find_component('therm_size_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        # elec_eff = model.find_component('elec_eff_' + self.name)
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_heat = model.find_component(
            'output_' + self.outputs[0] + '_' + self.name)
        output_elec = model.find_component(
            'output_' + self.outputs[1] + '_' + self.name)
        status = model.find_component('status_' + self.name)
        # todo: (qli) die Richtigkeit checken
        # model.cons.add(status[1] == 1)

        for t in model.time_step:
            model.cons.add(input_energy[t] * therm_eff[t] == output_heat[t])
            model.cons.add(Qth * status[t] == output_heat[t])
            model.cons.add(Pel * status[t] == output_elec[t])

    def add_cons(self, model):
        self._constraint_Pel(model)
        self._constraint_therm_eff(model)
        self._constraint_temp(model)
        self._constraint_conver(model)
        self._constraint_heat_outputs(model)
        self._constraint_vdi2067(model)

        # todo (qli): building.py Zeile 342 anpassen
        self._constraint_elec_balance(model)
        # todo (qli): building.py Zeile 342 anpassen
        self._constraint_heat_balance(model)

    def add_vars(self, model):
        super().add_vars(model)

        Qth = pyo.Var(bounds=(0, None))
        model.add_component('therm_size_' + self.name, Qth)

        therm_eff = pyo.Var(model.time_step, bounds=(0, 1))
        model.add_component('therm_eff_' + self.name, therm_eff)

        outlet_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('outlet_temp_' + self.name, outlet_temp)

        inlet_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('inlet_temp_' + self.name, inlet_temp)

        status = pyo.Var(model.time_step, domain=pyo.Binary)
        model.add_component('status_' + self.name, status)

        # todo (qli): building.py Zeile 342 anpassen
        # output_elec = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('output_elec_' + self.name, output_elec)

        # todo (qli): building.py Zeile 342 anpassen
        energy_flow_elec = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component(self.name + '_e_grid_elec', energy_flow_elec)

        # todo (qli): building.py Zeile 342 anpassen
        energy_flow_elec = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('chp_small_' + self.name + '_elec',
                            energy_flow_elec)

    # todo (qli): building.py Zeile 342 anpassen
    def _constraint_elec_balance(self, model):
        sell_elec = model.find_component(
            'output_' + self.outputs[1] + '_' + self.name)
        # todo (qli): Name anpassen ('chp_big_' + self.name + '_elec')3
        energy_flow_elec = model.find_component(self.name + '_e_grid_elec')
        for t in model.time_step:
            model.cons.add(sell_elec[t] == energy_flow_elec[t])

    # todo (qli): building.py Zeile 342 anpassen
    def _constraint_heat_balance(self, model):
        output_heat = model.find_component(
            'output_' + self.outputs[0] + '_' + self.name)
        # todo (qli): Name anpassen ('chp_big_' + self.name + '_elec')
        energy_flow_heat = model.find_component(self.name + '_water_tes')
        for t in model.time_step:
            model.cons.add(output_heat[t] == energy_flow_heat[t])

