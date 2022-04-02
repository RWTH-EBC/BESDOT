import os
import warnings

import pandas as pd
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction

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
        self.other_op_cost = True

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

    def _constraint_therm_eff_gdp(self, model):
        small_num = 0.00001
        Qth = model.find_component('therm_size_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        for t in model.time_step:
            a = Disjunct()
            c_1 = pyo.Constraint(expr=inlet_temp[t] <= 50)
            c_2 = pyo.Constraint(
                expr=therm_eff[t] == 0.705 - 0.0008 * (Qth - 44) - 0.006 * (
                            inlet_temp[t] - 30))
            model.add_component('a_dis_' + str(t), a)
            a.add_component('a_1' + str(t), c_1)
            a.add_component('a_2' + str(t), c_2)
            b = Disjunct()
            c_3 = pyo.Constraint(expr=inlet_temp[t] >= 50 + small_num)
            c_4 = pyo.Constraint(
                expr=therm_eff[t] == -0.0000355 * Qth + 0.498)
            model.add_component('b_dis_' + str(t), b)
            b.add_component('b_1' + str(t), c_3)
            b.add_component('b_2' + str(t), c_4)

            dj = Disjunction(expr=[a,b])
            model.add_component('dj_dis_' + str(t), dj)

    # verbinden die Parameter der einzelnen Anlage mit den Parametern zwischen
    # zwei Anlagen (simp_matrix).
    # Die Rücklauftemperatur der BHKW muss kleiner als 50 Grad sein,
    # damit der Brennwert ausgenutzt werden kann.
    # Zu hohe Temperaturspreizng (>25 Grad) führt zur Beschädigung der Anlagen.

    def _constraint_temp(self, model):
        outlet_temp = model.find_component('outlet_temp_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        #for t in model.time_step:
            # model.cons.add(outlet_temp[t] - inlet_temp[t] <= 25)
            # model.cons.add(inlet_temp[t] <= 50)
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
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_heat = model.find_component(
            'output_' + self.outputs[0] + '_' + self.name)
        output_elec = model.find_component(
            'output_' + self.outputs[1] + '_' + self.name)
        status = model.find_component('status_' + self.name)

        for t in model.time_step:
            model.cons.add(input_energy[t] * therm_eff[t] == output_heat[t])
            model.cons.add(Qth * status[t] == output_heat[t])
            model.cons.add(Pel * status[t] == output_elec[t])

    def add_cons(self, model):
        self._constraint_Pel(model)
        self._constraint_therm_eff_gdp(model)
        self._constraint_temp(model)
        self._constraint_conver(model)

        self._constraint_vdi2067_chp(model)
        self._constraint_start_stop_ratio_gdp(model)
        # todo (qli): building.py anpassen
        self._constraint_start_cost(model)
        # todo (qli): building.py anpassen
        self._constraint_chp_elec_sell_price(model)

    def add_vars(self, model):
        super().add_vars(model)

        Qth = pyo.Var(bounds=(7, 109))
        model.add_component('therm_size_' + self.name, Qth)

        therm_eff = pyo.Var(model.time_step, bounds=(0, 1))
        model.add_component('therm_eff_' + self.name, therm_eff)

        outlet_temp = pyo.Var(model.time_step, bounds=(12, 95))
        model.add_component('outlet_temp_' + self.name, outlet_temp)

        inlet_temp = pyo.Var(model.time_step, bounds=(12, 95))
        model.add_component('inlet_temp_' + self.name, inlet_temp)

        status = pyo.Var(model.time_step, domain=pyo.Binary)
        model.add_component('status_' + self.name, status)

        status1 = pyo.Var(range(1, len(model.time_step)+6), domain=pyo.Binary)
        model.add_component('status1_' + self.name, status1)

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

    def _constraint_start_stop_ratio_gdp(self, model):
        status = model.find_component('status_' + self.name)
        status1 = model.find_component('status1_' + self.name)
        model.cons.add(status1[1] == 0)
        for t in model.time_step:
            model.cons.add(status1[t+1] == status[t])
            model.cons.add(status1[len(model.time_step)+5] == 0)
            model.cons.add(status1[len(model.time_step)+4] == 0)
            model.cons.add(status1[len(model.time_step)+3] == 0)
            model.cons.add(status1[len(model.time_step)+2] == 0)
            model.cons.add(status1[len(model.time_step)+1] == 0)

        '''
        for t in model.time_step:
            if status1[t + 1] == 1 and status1[t] == 0:
                 model.cons.add(status1[t + 2] == 1)
                 model.cons.add(status1[t + 3] == 1)
                 model.cons.add(status1[t + 4] == 1)
                 model.cons.add(status1[t + 5] == 1)
                 model.cons.add(status1[t + 6] == 1)
        '''
        # len(model.time_step) >= 6
        for t in range(1, len(model.time_step)):
            d = Disjunct()
            c_5 = pyo.Constraint(expr=status1[t+1] - status1[t] == 1)
            c_6 = pyo.Constraint(expr=status1[t + 2] == 1)
            c_7 = pyo.Constraint(expr=status1[t + 3] == 1)
            c_8 = pyo.Constraint(expr=status1[t + 4] == 1)
            c_9 = pyo.Constraint(expr=status1[t + 5] == 1)
            c_10 = pyo.Constraint(expr=status1[t + 6] == 1)
            model.add_component('d_dis_' + str(t), d)
            d.add_component('d_1' + str(t), c_5)
            d.add_component('d_2' + str(t), c_6)
            d.add_component('d_3' + str(t), c_7)
            d.add_component('d_4' + str(t), c_8)
            d.add_component('d_5' + str(t), c_9)
            d.add_component('d_6' + str(t), c_10)
            e = Disjunct()
            c_11 = pyo.Constraint(expr=status1[t + 1] - status1[t] == 0)
            model.add_component('e_dis_' + str(t), e)
            e.add_component('e_1' + str(t), c_11)
            f = Disjunct()
            c_12 = pyo.Constraint(expr=status1[t + 1] - status1[t] == -1)
            model.add_component('f_dis_' + str(t), f)
            f.add_component('f_1' + str(t), c_12)

            dj = Disjunction(expr=[d, e, f])
            model.add_component('dj_dis1_' + str(t), dj)

    def _constraint_start_cost(self, model):
        status = model.find_component('status_' + self.name)
        start = model.find_component('start_' + self.name)
        # todo (qli): building.py anpassen
        start_cost = model.find_component('start_cost_' + self.name)
        status1 = model.find_component('status1_' + self.name)
        other_op_cost = model.find_component('other_op_cost_' + self.name)
        model.cons.add(status1[1] == 0)
        for t in model.time_step:
            model.cons.add(status1[t + 1] == status[t])
        for t in range(1, len(model.time_step)+1):
            g = Disjunct()
            c_13 = pyo.Constraint(expr=status1[t+1] - status1[t] == 1)
            c_14 = pyo.Constraint(expr=start[t] == 1)
            model.add_component('g_dis_' + str(t), g)
            g.add_component('g_1' + str(t), c_13)
            g.add_component('g_2' + str(t), c_14)
            h = Disjunct()
            c_15 = pyo.Constraint(expr=status1[t+1] - status1[t] == 0)
            c_16 = pyo.Constraint(expr=start[t] == 0)
            model.add_component('h_dis_' + str(t), h)
            h.add_component('h_1' + str(t), c_15)
            h.add_component('h_2' + str(t), c_16)
            i = Disjunct()
            c_17 = pyo.Constraint(expr=status1[t + 1] - status1[t] == -1)
            c_18 = pyo.Constraint(expr=start[t] == 0)
            model.add_component('i_dis_' + str(t), i)
            i.add_component('i_1' + str(t), c_17)
            i.add_component('i_2' + str(t), c_18)

            dj = Disjunction(expr=[g, h, i])
            model.add_component('dj_dis2_' + str(t), dj)

        model.cons.add(start_cost == self.start_price * sum(start[t] for t in
                                                            model.time_step))
        model.cons.add(other_op_cost == start_cost)

    def _constraint_chp_elec_sell_price(self, model):
        kwk_zuschlag = 0.08  # €/kWh
        stromspotmarktpreis = 0.179  # € / kWh
        elec_sell_price = model.find_component('elec_sell_price_' + self.name)
        model.cons.add(elec_sell_price == kwk_zuschlag + stromspotmarktpreis)
