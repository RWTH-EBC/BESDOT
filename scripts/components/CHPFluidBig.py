import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.CHP import CHP
from tools.calc_annuity_vdi2067 import calc_annuity

# große BHKW (Pel >= 50kW) ohne Brennwertnutzung
class CHPFluidBig(CHP, FluidComponent):

    def __init__(self, comp_name, comp_type="CHPFluidBig", comp_model=None,
                 min_size=50, max_size=400, current_size=0):
        # self.inputs = ['gas']
        # self.outputs = ['heat', 'elec']
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

    # todo (qli): building.py Zeile 342 anpassen
    def add_heat_flows_in(self, bld_heat_flows):
        # check the building heat flows and select the tuples related to this
        # device to add into list heat_flows.
        for element in bld_heat_flows:
            if element[1] != 'e_grid' and self.name == element[1]:
                self.heat_flows_in.append(element)

    # todo (qli): building.py Zeile 342 anpassen
    def add_heat_flows_out(self, bld_heat_flows):
        # check the building heat flows and select the tuples related to this
        # device to add into list heat_flows.
        for element in bld_heat_flows:
            if element[1] != 'e_grid'  and self.name == element[0]:
                self.heat_flows_out.append(element)

    # Pel = elektrische Nennleistung = comp_size
    # Qth = thermische Nennleistung
    def _constraint_Pel(self, model):
        Pel = model.find_component('size_' + self.name)
        Qth = model.find_component('therm_size_' + self.name)
        # todo: Korrektur
        model.cons.add(Pel == 0.8148 * Qth - 16.89)

    def _constraint_therm_eff(self, model):
        Qth = model.find_component('therm_size_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        outlet_temp = model.find_component('outlet_temp_' + self.name)
        for t in model.time_step:
            model.cons.add(
                therm_eff[t] == 0.496 - 0.0001 * (Qth - 267) - 0.002 * (
                            inlet_temp[t] - 47) - 0.0017 * (
                            outlet_temp[t] - 67))

    def _constraint_temp(self, model):
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
                model.cons.add(outlet_temp[t] - inlet_temp[t] <= 25)

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
        self._constraint_therm_eff(model)
        self._constraint_temp(model)
        self._constraint_conver(model)
        self._constraint_heat_outputs(model)
        # todo (qli): building.py Zeile 342 anpassen
        self._constraint_elec_balance(model)
        # todo (qli): building.py Zeile 342 anpassen
        self._constraint_heat_balance(model)
        self._constraint_vdi2067_chp(model)
        self._constraint_start_stop_ratio(model)
        # todo (qli): building.py anpassen
        self._constraint_start_cost(model)
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

    # todo (qli): building.py anpassen
    def _constraint_elec_balance(self, model):
        sell_elec = model.find_component(
            'output_' + self.outputs[1] + '_' + self.name)
        energy_flow_elec = model.find_component(self.name + '_e_grid_elec')
        for t in model.time_step:
            model.cons.add(sell_elec[t] == energy_flow_elec[t])

    # todo (qli): building.py anpassen
    def _constraint_heat_balance(self, model):
        output_heat = model.find_component(
            'output_' + self.outputs[0] + '_' + self.name)
        energy_flow_heat = model.find_component(self.name + '_water_tes')
        for t in model.time_step:
            model.cons.add(output_heat[t] == energy_flow_heat[t])

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
                 model.cons.add(status[t + 6] == 1)
                 model.cons.add(start[t + 1] == 1)
            if status[1] == 1:
                model.cons.add(start[1] == 1)
            else:
                model.cons.add(start[t + 1] == 0)
            
        '''
        pass

    def _constraint_start_cost(self, model):
        start_times = model.find_component('start_' + self.name)
        # todo (qli): building.py anpassen
        start_cost = model.find_component('start_cost_' + self.name)
        model.cons.add(start_cost == self.start_price * sum(start_times[t] for
                       t in model.time_step))

    def _constraint_chp_elec_sell_price(self, model):
        kwk_zuschlag = 0.08  # €/kWh
        stromspotmarktpreis = 0.167  # € / kWh
        elec_sell_price = model.find_component('elec_sell_price_' + self.name)
        model.cons.add(elec_sell_price == kwk_zuschlag + stromspotmarktpreis)
