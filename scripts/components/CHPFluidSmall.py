import os
import warnings

import pandas as pd
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.CHP import CHP
from tools.calc_annuity_vdi2067 import calc_annuity

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

        # todo (qli): start_price
        self.start_price = 5  # €/start
        # todo (qli): building.py Zeile 342 anpassen
        self.heat_flows_in = None
        self.heat_flows_out = []

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
            # model.cons.add(outlet_temp[t] - inlet_temp[t] <= 25)
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

        self._constraint_vdi2067_chp(model)
        #self._constraint_start_stop_ratio(model)
        # todo (qli): building.py anpassen
        #self._constraint_start_cost(model)
        # todo (qli): building.py anpassen
        self._constraint_chp_elec_sell_price(model)

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

        # output_elec = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('output_elec_' + self.name, output_elec)

        # todo (qli): building.py anpassen
        energy_flow_elec = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component(self.name + '_e_grid_elec', energy_flow_elec)

        # todo (qli): building.py anpassen
        energy_flow_elec = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('chp_small_' + self.name + '_elec',
                            energy_flow_elec)

        # todo (qli): building.py anpassen
        start_cost = pyo.Var(bounds=(0, None))
        model.add_component('start_cost_' + self.name, start_cost)

        start = pyo.Var(model.time_step, domain=pyo.Binary)
        model.add_component('start_' + self.name, start)

        # todo (qli): building.py anpassen
        elec_sell_price = pyo.Var(bounds=(0, None))
        model.add_component('elec_sell_price_' + self.name, elec_sell_price)

    def _constraint_vdi2067_chp(self, model):
        """
        t: observation period in years
        r: price change factor (not really relevant since we have n=0)
        q: interest factor
        n: number of replacements
        """
        size = model.find_component('size_' + self.name)
        annual_cost = model.find_component('annual_cost_' + self.name)
        invest = model.find_component('invest_' + self.name)
        # todo(qli): WÜ Preis
        model.cons.add(size * 458 + 57433 == invest)
        annuity = calc_annuity(self.life, invest, self.f_inst, self.f_w,
                               self.f_op)
        model.cons.add(annuity == annual_cost)

    def _constraint_start_stop_ratio(self, model):
        status = model.find_component('status_' + self.name)
        # todo (qli): GDP Modell
        '''
        for t in model.time_step:
            if status[t + 1] == 1 and status[t] == 0:
                 model.cons.add(status[t + 2] == 1)
                 model.cons.add(status[t + 3] == 1)
                 model.cons.add(status[t + 4] == 1)
                 model.cons.add(status[t + 5] == 1)
                 model.cons.add(status[t + 5] == 1)
        '''
        pass

    def _constraint_start_cost(self, model):
        status = model.find_component('status_' + self.name)
        # todo (qli): building.py anpassen
        start_cost = model.find_component('start_cost_' + self.name)
        model.cons.add(start_cost == self.start_price * sum(status[t] for t in
                       model.time_step))

    def _constraint_chp_elec_sell_price(self, model):
        kwk_zuschlag = 0.08  # €/kWh
        stromspotmarktpreis = 0.179  # € / kWh
        elec_sell_price = model.find_component('elec_sell_price_' + self.name)
        model.cons.add(elec_sell_price == kwk_zuschlag + stromspotmarktpreis)