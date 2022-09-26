import warnings
import pyomo.environ as pyo
from pyomo.core import lor
from pyomo.gdp import Disjunct, Disjunction

from scripts.FluidComponent import FluidComponent
from scripts.components.CHP import CHP
from tools.calc_annuity_vdi2067 import calc_annuity

small_num = 0.0001


# kleine BHKW (Pel <= 50kW) ohne Brennwertnutzung
class CHPFluidSmallHi(CHP, FluidComponent):

    def __init__(self, comp_name, comp_type="CHPFluidSmallHi", comp_model=None,
                 min_size=0, max_size=50, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.start_price = 5  # €/start
        self.heat_flows_in = None
        self.heat_flows_out = []
        self.other_op_cost = True

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if 'outlet temperature' in properties.columns:
            self.outlet_temp = float(properties['outlet temperature'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for outlet temperature.")
            # EC_POWER_DE_Technisches_Datenblatt
            self.outlet_temp = 80

    # Pel = elektrische Nennleistung = comp_size
    # Qth = thermische Nennleistung
    # Qth = f(Pel)
    def _constraint_Pel(self, model):
        Pel = model.find_component('size_' + self.name)
        Qth = model.find_component('therm_size_' + self.name)
        model.cons.add(Pel == 0.551 * Qth - 1.7544)

    def _constraint_therm_eff(self, model):
        Qth = model.find_component('therm_size_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        model.cons.add(therm_eff == -0.0000355 * Qth + 0.498)

    # verbinden die Parameter der einzelnen Anlage mit den Parametern zwischen
    # zwei Anlagen (simp_matrix).
    def _constraint_temp(self, model):
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] + '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] + '_' + 'temp')
            for t in model.time_step:
                model.cons.add(self.outlet_temp == t_out[t])
                model.cons.add(inlet_temp[t] == t_in[t])

    # status_chp ----- zur Beschreibung der taktenden Betrieb
    # input * η = output
    def _constraint_conver(self, model):
        Pel = model.find_component('size_' + self.name)
        Qth = model.find_component('therm_size_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        input_energy = model.find_component('input_' + self.inputs[0] + '_' + self.name)
        output_heat = model.find_component('output_' + self.outputs[0] + '_' + self.name)
        output_elec = model.find_component('output_' + self.outputs[1] + '_' + self.name)
        status = model.find_component('status_' + self.name)

        for t in model.time_step:
            model.cons.add(input_energy[t] * therm_eff == output_heat[t])
            model.cons.add(Qth * status[t + 1] == output_heat[t])
            model.cons.add(Pel * status[t + 1] == output_elec[t])


    def _constraint_vdi2067_chp(self, model):
        size = model.find_component('size_' + self.name)
        annual_cost = model.find_component('annual_cost_' + self.name)
        invest = model.find_component('invest_' + self.name)

        model.cons.add(size * 1131.2 + 14490 == invest)
        annuity = calc_annuity(self.life, invest, self.f_inst, self.f_w, self.f_op)
        model.cons.add(annuity == annual_cost)

    def _constraint_vdi2067_chp_gdp(self, model):
        annual_cost = model.find_component('annual_cost_' + self.name)
        invest = model.find_component('invest_' + self.name)
        Pel = model.find_component('size_' + self.name)
        Qth = model.find_component('therm_size_' + self.name)

        if self.min_size == 0:
            min_size = small_num
        else:
            min_size = self.min_size

        dis_not_select = Disjunct()
        not_select_size = pyo.Constraint(expr=Pel == 0)
        not_select_inv = pyo.Constraint(expr=invest == 0)
        not_select_therm_size = pyo.Constraint(expr=Qth == 0)
        model.add_component('dis_not_select_' + self.name, dis_not_select)
        dis_not_select.add_component('not_select_size_' + self.name, not_select_size)
        dis_not_select.add_component('not_select_inv_' + self.name, not_select_inv)
        dis_not_select.add_component('not_select_therm_size_' + self.name, not_select_therm_size)

        dis_select = Disjunct()
        select_size = pyo.Constraint(expr=Pel >= min_size)
        select_inv = pyo.Constraint(expr=invest == Pel * 1131.2 + 14490)
        select_therm_size = pyo.Constraint(expr=Pel == 0.551 * Qth - 1.7544)
        model.add_component('dis_select_' + self.name, dis_select)
        dis_select.add_component('select_size_' + self.name,  select_size)
        dis_select.add_component('select_inv_' + self.name, select_inv)
        dis_select.add_component('select_therm_size_' + self.name, select_therm_size)

        dj_size = Disjunction(expr=[dis_not_select, dis_select])
        model.add_component('disjunction_size' + self.name, dj_size)

        annuity = calc_annuity(self.life, invest, self.f_inst, self.f_w, self.f_op)
        model.cons.add(annuity == annual_cost)

    def _constraint_start_stop_ratio_gdp(self, model):
        status = model.find_component('status_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        # start = model.find_component('start_' + self.name)
        model.cons.add(status[1] == 0)
        for t in model.time_step:
            if t == model.time_step[-1]:
                model.cons.add(status[len(model.time_step) + 5] == 0)
                model.cons.add(status[len(model.time_step) + 4] == 0)
                model.cons.add(status[len(model.time_step) + 3] == 0)
                model.cons.add(status[len(model.time_step) + 2] == 0)
                model.cons.add(status[len(model.time_step) + 1] == 0)

        # len(model.time_step) >= 6
        for t in range(1, len(model.time_step)):
            d1 = Disjunct()
            c_5 = pyo.Constraint(expr=status[t + 1] - status[t] == 1)
            c_6 = pyo.Constraint(expr=status[t + 2] == 1)
            c_7 = pyo.Constraint(expr=status[t + 3] == 1)
            c_8 = pyo.Constraint(expr=status[t + 4] == 1)
            c_9 = pyo.Constraint(expr=status[t + 5] == 1)
            c_10 = pyo.Constraint(expr=status[t + 6] == 1)
            c_13 = pyo.Constraint(expr=inlet_temp[t] <= 70)
            # c_18 = pyo.Constraint(expr=start[t] == 1)
            model.add_component('d1_dis_' + str(t), d1)
            d1.add_component('d1_1' + str(t), c_5)
            d1.add_component('d1_2' + str(t), c_6)
            d1.add_component('d1_3' + str(t), c_7)
            d1.add_component('d1_4' + str(t), c_8)
            d1.add_component('d1_5' + str(t), c_9)
            d1.add_component('d1_6' + str(t), c_10)
            d1.add_component('d1_7' + str(t), c_13)
            # d1.add_component('d1_8' + str(t), c_18)

            e1 = Disjunct()
            c_11 = pyo.Constraint(expr=status[t + 1] == 0)
            c_14 = pyo.Constraint(expr=status[t] == 0)
            # c_19 = pyo.Constraint(expr=start[t] == 0)
            model.add_component('e1_dis_' + str(t), e1)
            e1.add_component('e1_1' + str(t), c_11)
            e1.add_component('e1_2' + str(t), c_14)
            # e1.add_component('e1_3' + str(t), c_19)

            y1 = Disjunct()
            c_15 = pyo.Constraint(expr=status[t + 1] == 1)
            c_16 = pyo.Constraint(expr=status[t] == 1)
            c_17 = pyo.Constraint(expr=inlet_temp[t + 1] <= 70)
            # c_20 = pyo.Constraint(expr=start[t] == 0)
            model.add_component('y1_dis_' + str(t), y1)
            y1.add_component('y1_1' + str(t), c_15)
            y1.add_component('y1_2' + str(t), c_16)
            y1.add_component('y1_3' + str(t), c_17)
            # y1.add_component('y1_4' + str(t), c_20)

            f1 = Disjunct()
            c_12 = pyo.Constraint(expr=status[t + 1] - status[t] == -1)
            # c_21 = pyo.Constraint(expr=start[t] == 0)
            model.add_component('f1_dis_' + str(t), f1)
            f1.add_component('f1_1' + str(t), c_12)
            # f1.add_component('f1_2' + str(t), c_21)

            dj1 = Disjunction(expr=[d1, e1, y1, f1])
            model.add_component('dj1_dis_' + str(t), dj1)

    # konstanter Massenstrom
    def _constraint_mass_flow(self, model):
        for heat_output in self.heat_flows_out:
            m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'mass')
            for t in range(len(model.time_step) - 1):
                model.cons.add(m_in[t + 1] == m_out[t + 1])
                model.cons.add(m_in[t + 2] == m_in[t + 1])

    def _constraint_start_cost(self, model):
        start = model.find_component('start_' + self.name)
        start_cost = model.find_component('start_cost_' + self.name)
        other_op_cost = model.find_component('other_op_cost_' + self.name)
        model.cons.add(start_cost == self.start_price * sum(start[t] for t in model.time_step))
        model.cons.add(other_op_cost == start_cost)

    def _constraint_status(self, model):
        period_length = 24
        status = model.find_component('status_' + self.name)

        for t in range(2, len(model.time_step) + 6):
            if t % period_length == 0:
                model.cons.add(status[t] == 0)

    def add_cons(self, model):
        self._constraint_therm_eff(model)
        self._constraint_temp(model)
        self._constraint_conver(model)
        self._constraint_heat_outputs(model)
        self._constraint_start_stop_ratio_gdp(model)
        self._constraint_Pel(model)
        self._constraint_vdi2067_chp(model)
        self._constraint_status(model)
        # self._constraint_mass_flow(model)
        # self._constraint_vdi2067_chp_gdp(model)
        # self._constraint_start_cost(model)

    def add_vars(self, model):
        super().add_vars(model)

        Qth = pyo.Var(bounds=(6.8, 94))
        model.add_component('therm_size_' + self.name, Qth)

        therm_eff = pyo.Var(bounds=(0, 1))
        model.add_component('therm_eff_' + self.name, therm_eff)

        inlet_temp = pyo.Var(model.time_step, bounds=(12, 80))
        model.add_component('inlet_temp_' + self.name, inlet_temp)

        status = pyo.Var(range(1, len(model.time_step) + 6), domain=pyo.Binary)
        model.add_component('status_' + self.name, status)

        # outlet_temp = pyo.Var(model.time_step, bounds=(12, 95))
        # model.add_component('outlet_temp_' + self.name, outlet_temp)

        # start_cost = pyo.Var(bounds=(0, None))
        # model.add_component('start_cost_' + self.name, start_cost)

        # start = pyo.Var(model.time_step, domain=pyo.Binary)
        # model.add_component('start_' + self.name, start)