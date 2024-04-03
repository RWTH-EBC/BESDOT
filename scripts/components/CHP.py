import warnings
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Component import Component
from utils.calc_annuity_vdi2067 import calc_annuity

small_num = 0.0001


class CHP(Component):

    def __init__(self, comp_name, comp_type="CHP", comp_model=None,
                 min_size=0, max_size=1000, current_size=0, sub_model="large"):
        self.inputs = ['gas']
        self.outputs = ['heat', 'elec']
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.sub_model = sub_model
        self.start_price = 5  # €/start
        self.other_op_cost = False

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if 'el_efficiency' in properties.columns:
            self.efficiency['elec'] = float(properties['el_efficiency'])
        if 'th_efficiency' in properties.columns:
            self.efficiency['heat'] = float(properties['th_efficiency'])

    def _constraint_vdi2067(self, model):
        """The price information does not come from the crawler, but the
        report of ASUE, which provides the curve from regression. The exact
        price of each device was not given. So the data could not be updated
        and using linearization to get the cost model 0 and 1. The cost model 2
        could not be generated from the curve."""
        size = model.find_component('size_' + self.name)
        annual_cost = model.find_component('annual_cost_' + self.name)
        invest = model.find_component('invest_' + self.name)
        city_subsidy = model.find_component('city_subsidy_' + self.name)
        state_subsidy = model.find_component('state_subsidy_' + self.name)
        country_subsidy = model.find_component('country_subsidy_' + self.name)

        if self.min_size == 0:
            min_size = small_num
        else:
            min_size = self.min_size

        if self.cost_model == 0:
            if self.sub_model == "small":
                self.unit_cost = 1568  # €/el kW
            elif self.sub_model == "condensing":
                self.unit_cost = 1568 + 76  # €/el kW
            model.cons.add(size * self.unit_cost)
        elif self.cost_model == 1:
            if self.sub_model == "small":
                self.unit_cost = 1131.2  # €/el kW
                self.fixed_cost = 14490  # €
            elif self.sub_model == "condensing":
                self.unit_cost = 1568 + 76  # €/el kW
                self.fixed_cost = 14490  # €

            if self.sub_model == "small" or self.sub_model == "condensing":
                dis_not_select = Disjunct()
                not_select_size = pyo.Constraint(expr=size == 0)
                not_select_inv = pyo.Constraint(expr=invest == 0)
                model.add_component('dis_not_select_' + self.name,
                                    dis_not_select)
                dis_not_select.add_component('not_select_size_' + self.name,
                                             not_select_size)
                dis_not_select.add_component('not_select_inv_' + self.name,
                                             not_select_inv)

                dis_select = Disjunct()
                select_size = pyo.Constraint(expr=size >= min_size)
                select_inv = pyo.Constraint(expr=invest == size *
                                                 self.unit_cost +
                                                 self.fixed_cost)
                model.add_component('dis_select_' + self.name, dis_select)
                dis_not_select.add_component('select_size_' + self.name,
                                             select_size)
                dis_not_select.add_component('select_inv_' + self.name,
                                             select_inv)

                dj_size = Disjunction(expr=[dis_not_select, dis_select])
                model.add_component('disjunction_vdi_' + self.name, dj_size)

                dis_select_small = Disjunct()
                select_small_size_lower = pyo.Constraint(expr=size >= min_size)
                select_small_size_upper = pyo.Constraint(expr=size <= 50)
                select_small_inv = pyo.Constraint(expr=invest == size *
                                                       1131.2 + 14490)
                model.add_component('dis_select_small_' + self.name,
                                    dis_select_small)
                dis_select_small.add_component(
                    'select_small_size_lower_' + self.name,
                    select_small_size_lower)
                dis_select_small.add_component(
                    'select_small_size_upper_' + self.name,
                    select_small_size_upper)
                dis_select_small.add_component('select_small_inv_' +
                                               self.name, select_small_inv)

                dj_size = Disjunction(expr=[dis_not_select, dis_select_small])
                model.add_component('disjunction_vdi_' + self.name, dj_size)
        elif self.cost_model == 2:
            warnings.warn(self.name + " is CHP, which has no data pair for "
                                      "price, the cost model 2 is not allowed.")

        # model.cons.add(size * 458 + 57433 == invest)
        annuity = calc_annuity(self.life, invest - city_subsidy, self.f_inst, self.f_w, self.f_op)
        model.cons.add(annuity == annual_cost)

    def _constraint_power(self, model):
        """This method shows the relationship of electricity power and thermal
        power of a CHP. The relationship are derived from regression of
        ASUE's product tables.
        The parameter for the relations are hard coded. If the model
        technical is changed, the relationship should be updated. And it
        would be better, if the relationship could be set by user.
        power_el: electricity power, which is defined as comp_size
        power_th: thermal nominal power

        The sub model contains the products smaller than 50 kW, so a GDP
        model is used here.
        """
        power_el = model.find_component('size_' + self.name)
        power_th = model.find_component('therm_size_' + self.name)
        if self.sub_model == "small":
            model.cons.add(power_th == 2.1178 * power_el + 2.5991)
        elif self.sub_model == "condensing":
            model.cons.add(power_el == 0.551 * power_th - 1.7544)
            if model.find_component('select_small_' + self.name):
                select_small = model.find_component('select_small_' + self.name)
            else:
                select_small = Disjunct()
                model.add_component('select_small_' + self.name, select_small)
                select_small_size = pyo.Constraint(expr=power_el <= 50)
                select_small.add_component('select_small_size_' + self.name,
                                           select_small_size)
            select_small_relation = \
                pyo.Constraint(expr=power_th == 2.1178 * power_el + 2.5991)
            select_small.add_component('select_small_relation_' + self.name,
                                       select_small_relation)

            if not model.find_component('select_large_' + self.name):
                dj_power = Disjunction(expr=select_small)
                model.add_component('disjunction_power_' + self.name, dj_power)

    def _constraint_start_stop_ratio(self, model):
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
            k = Disjunct()
            c_5 = pyo.Constraint(expr=status[t + 1] - status[t] == 1)
            c_6 = pyo.Constraint(expr=status[t + 2] == 1)
            c_7 = pyo.Constraint(expr=status[t + 3] == 1)
            c_8 = pyo.Constraint(expr=status[t + 4] == 1)
            c_9 = pyo.Constraint(expr=status[t + 5] == 1)
            c_10 = pyo.Constraint(expr=status[t + 6] == 1)
            # c_12 = pyo.Constraint(expr=start[t] == 1)
            model.add_component('k_dis_' + str(t), k)
            k.add_component('k_1' + str(t), c_5)
            k.add_component('k_2' + str(t), c_6)
            k.add_component('k_3' + str(t), c_7)
            k.add_component('k_4' + str(t), c_8)
            k.add_component('k_5' + str(t), c_9)
            k.add_component('k_6' + str(t), c_10)
            # k.add_component('k_7' + str(t), c_12)

            l = Disjunct()
            c_11 = pyo.Constraint(expr=status[t + 1] == 0)
            c_13 = pyo.Constraint(expr=status[t] == 0)
            # c_14 = pyo.Constraint(expr=start[t] == 0)
            model.add_component('l_dis_' + str(t), l)
            l.add_component('l_1' + str(t), c_11)
            l.add_component('l_2' + str(t), c_13)
            # l.add_component('l_3' + str(t), c_14)

            n = Disjunct()
            c_15 = pyo.Constraint(expr=status[t + 1] == 1)
            c_16 = pyo.Constraint(expr=status[t] == 1)
            c_17 = pyo.Constraint(expr=inlet_temp[t + 1] <= 70)
            # c_18 = pyo.Constraint(expr=start[t] == 0)
            model.add_component('n_dis_' + str(t), n)
            n.add_component('n_1' + str(t), c_15)
            n.add_component('n_2' + str(t), c_16)
            n.add_component('n_3' + str(t), c_17)
            # n.add_component('n_4' + str(t), c_18)

            m = Disjunct()
            c_12 = pyo.Constraint(expr=status[t + 1] - status[t] == -1)
            # c_19 = pyo.Constraint(expr=start[t] == 0)
            model.add_component('m_dis_' + str(t), m)
            m.add_component('m_1' + str(t), c_12)
            # m.add_component('m_2' + str(t), c_19)

            dj = Disjunction(expr=[k, l, m, n])
            model.add_component('dj_dis3_' + str(t), dj)

    def _constraint_start_cost(self, model):
        start = model.find_component('start_' + self.name)
        start_cost = model.find_component('start_cost_' + self.name)
        other_op_cost = model.find_component('other_op_cost_' + self.name)
        model.cons.add(start_cost == self.start_price * sum(start[t] for t in
                                                            model.time_step))
        model.cons.add(other_op_cost == start_cost)

    def _constraint_status(self, model):
        """
        The status is set to 0 every 24 hours.
        """
        period_length = 24
        status = model.find_component('status_' + self.name)

        for t in range(2, len(model.time_step) + 6):
            if t % period_length == 0:
                model.cons.add(status[t] == 0)

    def _constraint_conver_puls(self, model):
        """
        status_chp ----- zur Beschreibung der taktenden Betrieb
        input * η = output
        """
        size = model.find_component('size_' + self.name)
        therm_size = model.find_component('therm_size_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        input_energy = model.find_component(
            'input_' + self.inputs[0] + '_' + self.name)
        output_heat = model.find_component(
            'output_' + self.outputs[0] + '_' + self.name)
        output_elec = model.find_component(
            'output_' + self.outputs[1] + '_' + self.name)
        status = model.find_component('status_' + self.name)

        for t in model.time_step:
            model.cons.add(input_energy[t] * therm_eff[t] == output_heat[t])
            model.cons.add(therm_size * status[t + 1] == output_heat[t])
            model.cons.add(size * status[t + 1] == output_elec[t])

    def add_cons(self, model):
        super().add_cons(model)

        # self._constraint_start_stop_ratio(model)
        self._constraint_power(model)
        # unnecessary methods, could be called by demand.
        # self._constraint_status(model)
        # self._constraint_conver_puls(model)
        # self._constraint_start_cost(model)

    def add_vars(self, model):
        super().add_vars(model)

        therm_size = pyo.Var(bounds=(0, 600))
        model.add_component('therm_size_' + self.name, therm_size)

        status = pyo.Var(range(1, len(model.time_step) + 6), domain=pyo.Binary)
        model.add_component('status_' + self.name, status)
