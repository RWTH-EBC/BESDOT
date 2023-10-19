import os
import warnings
import pandas as pd
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from utils.calc_annuity_vdi2067 import calc_annuity
# from scripts.subsidies.city_subsidy import CitySubsidyComponent
# from scripts.subsidies.state_subsidy import StateSubsidyComponent
# from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyComponent

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

small_num = 0.0001


class Component(object):
    def __init__(self, comp_name, comp_type="Component", comp_model=None,
                 min_size=0, max_size=1000, current_size=0, cost_model=0):
        self.name = comp_name
        self.component_type = comp_type
        self.comp_model = comp_model

        if not hasattr(self, 'inputs'):
            self.inputs = []
        if not hasattr(self, 'outputs'):
            self.outputs = []
        self.efficiency = {'elec': None,
                           'heat': None,
                           'cool': None}

        self.min_size = min_size
        self.max_size = max_size
        self.current_size = current_size

        if cost_model in [0, 1, 2]:
            self.cost_model = cost_model
        else:
            warn_msg = 'Unexpected cost model ' + str(cost_model) + \
                       ' is given for the component ' + self.name
            warnings.warn(warn_msg)
            self.cost_model = 0
        self.unit_cost = None
        self.fixed_cost = None
        self.cost_pair = None
        self.components = {}
        self.subsidy_list = []

        self.energy_flows = {'input': {},
                             'output': {}}

        # Read the data from database
        if comp_model is not None:
            properties = self.get_properties(comp_model)
            self._read_properties(properties)

        self.other_op_cost = False

    def get_properties(self, model):
        model_property_file = os.path.join(base_path, 'data',
                                           'component_database',
                                           self.component_type,
                                           model + '.csv')
        properties = pd.read_csv(model_property_file)
        return properties

    def _read_properties(self, properties):
        # todo (yni): modify the function formate and database formate
        if self.outputs is not None:
            if 'efficiency' in properties.columns:
                self.efficiency[self.outputs[0]] = float(
                    properties['efficiency'])
            else:
                if self.component_type not in ['Storage', 'Inverter',
                                               'Battery', 'HotWaterStorage',
                                               'PV']:
                    warnings.warn("In the model database for " + self.name +
                                  " lack of column for efficiency.")
        if 'service life' in properties.columns:
            self.life = int(properties['service life'])
        elif 'service_life' in properties.columns:
            self.life = int(properties['service_life'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for service life.")
        if 'factor repair effort' in properties.columns:
            self.f_inst = float(properties['factor repair effort'])
        elif 'factor_repair_effort' in properties.columns:
            self.f_inst = float(properties['factor_repair_effort'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for factor repair effort.")
        if 'factor servicing effort' in properties.columns:
            self.f_w = float(properties['factor servicing effort'])
        elif 'factor_servicing_effort' in properties.columns:
            self.f_w = float(properties['factor_servicing_effort'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for factor servicing effort.")
        if 'servicing effort hours' in properties.columns:
            self.f_op = float(properties['servicing effort hours'])
        elif 'servicing_effort_hours' in properties.columns:
            self.f_op = float(properties['servicing_effort_hours'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for servicing effort hours.")

        if self.cost_model == 0:
            if 'only-unit-price' in properties.columns:
                self.unit_cost = float(properties['only-unit-price'])
            else:
                warnings.warn("In the model database for " + self.name +
                              "lack of column for unit cost. Its cost model "
                              "was changed to 0")
        elif self.cost_model == 1:
            if 'fixed-unit-price' in properties.columns and \
                    'fixed-price' in properties.columns:
                self.unit_cost = float(properties['fixed-unit-price'])
                self.fixed_cost = float(properties['fixed-price'])
            elif 'fixed-unit-price' not in properties.columns:
                warnings.warn("In the model database for " + self.name +
                              " lack of column for unit cost. Its cost model "
                              "was changed to 0")
                self.change_cost_model(0)
            elif 'fixed-price' not in properties.columns:
                warnings.warn("In the model database for " + self.name +
                              " lack of column for fixed price. Its cost "
                              "model was changed to 0")
                self.change_cost_model(0)
            else:
                warnings.warn("In the model database for " + self.name +
                              " lack of column for unit cost and fixed price. "
                              "Its cost model was changed to 0")
                self.change_cost_model(0)
        elif self.cost_model == 2:
            if 'data-pair' in properties.columns:
                self.cost_pair = properties['data-pair'].values[0].split('/')
            else:
                warnings.warn("In the model database for " + self.name +
                              " lack of column for data pair and fixed price. "
                              "Its cost model was changed to 0")
                self.change_cost_model(0)

    def update_profile(self, **kwargs):
        for arg in kwargs:
            if hasattr(self, arg):
                setattr(self, arg, kwargs[arg])
            else:
                warnings.warn("Can't update the profile for component" +
                              self.name)

    def to_dict(self):
        return {
            "name": self.name,
            "component_type": self.component_type,
            "comp_model": self.comp_model,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "efficiency": self.efficiency,
            "min_size": int(self.min_size),
            "max_size": int(self.max_size),
            "current_size": int(self.current_size),
            "cost_model": self.cost_model,
            "unit_cost": self.unit_cost,
            "fixed_cost": self.fixed_cost,
            "cost_pair": self.cost_pair,
            "energy_flows": self.energy_flows,
            "other_op_cost": self.other_op_cost,
            "subsidy": self.subsidy_list
        }

    def add_energy_flows(self, io, energy_type, energy_flow):
        if io in ['input', 'output']:
            if energy_type not in self.energy_flows[io].keys():
                self.energy_flows[io][energy_type] = []
            self.energy_flows[io][energy_type].append(energy_flow)
        else:
            warnings.warn("io of the function add_energy_flow only allowed "
                          "for 'input' or 'output'.")

    """
    def add_subsidy(self, subsidy):
        if subsidy == 'all':
            all_subsidies = []

            for subsidy_comp in self.subsidy_list:
                if isinstance(subsidy_comp, CitySubsidyComponent):
                    all_subsidies.append(subsidy_comp)
                elif isinstance(subsidy_comp, CountrySubsidyComponent):
                    all_subsidies.append(subsidy_comp)

            for subsidy_comp in all_subsidies:
                subsidy_comp.analyze_topo(self)

            self.subsidy_list.extend(all_subsidies)

        elif isinstance(subsidy, (CitySubsidyComponent, CountrySubsidyComponent)):
            self.subsidy_list.append(subsidy)
            subsidy.analyze_topo(self)
        else:
            warnings.warn("The subsidy " + subsidy + " was not modeled, check again, "
                          "if something goes wrong.")
    """

    def show_cost_model(self):
        print("The cost model for model " + self.name + " is " +
              str(self.cost_model))

    def change_cost_model(self, new_cost_model):
        if new_cost_model in [0, 1, 2]:
            self.cost_model = new_cost_model
        else:
            warn_msg = 'Unexpected cost model ' + str(new_cost_model) + \
                       ' for change_cost_model() of ' + self.name
            warnings.warn(warn_msg)
            self.cost_model = 0

        self.unit_cost = None
        self.fixed_cost = None
        self.cost_pair = None

        if self.comp_model is not None:
            properties = self.get_properties(self.comp_model)
            self._read_properties(properties)

    def _constraint_conver(self, model):
        # todo: the component with more than one input is not developed,
        #  because of the easily confused efficiency. If meet component in
        #  this type, develop the method further. (By mixing of natural gas
        #  and hydrogen, or special electrolyzer, which need heat and
        #  electricity at the same time)

        for output in self.outputs:
            output_energy = model.find_component('output_' + output + '_' +
                                                 self.name)
            if self.inputs is None:
                break
            elif len(self.inputs) == 1:
                input_energy = model.find_component('input_' + self.inputs[0] +
                                                    '_' + self.name)
            else:
                input_energy = None  # for more than 1 input, should be
                # developed

            for t in model.time_step:
                model.cons.add(output_energy[t] == input_energy[t] *
                               self.efficiency[output])

    def _constraint_maxpower(self, model):
        if self.outputs is not None:
            size = model.find_component('size_' + self.name)
            if len(self.outputs) == 1:
                output_powers = model.find_component('output_' +
                                                     self.outputs[0] + '_' +
                                                     self.name)
            else:
                if 'elec' in self.outputs:
                    output_powers = model.find_component('output_elec_' +
                                                         self.name)
                else:
                    output_powers = model.find_component('output_' +
                                                         self.outputs[0] + '_' +
                                                         self.name)

            for t in model.time_step:
                model.cons.add(output_powers[t] <= size)

    def _constraint_vdi2067(self, model):
        size = model.find_component('size_' + self.name)
        invest = model.find_component('invest_' + self.name)
        annual_cost = model.find_component('annual_cost_' + self.name)
        city_subsidy = model.find_component('city_subsidy_' + self.name)
        state_subsidy = model.find_component('state_subsidy_' + self.name)
        country_subsidy = model.find_component('country_subsidy_' + self.name)

        if self.min_size == 0:
            min_size = small_num
        else:
            min_size = self.min_size

        if self.cost_model == 0:
            model.cons.add(invest == size * self.unit_cost)
        elif self.cost_model == 1:
            dis_not_select = Disjunct()
            not_select_size = pyo.Constraint(expr=size == 0)
            not_select_inv = pyo.Constraint(expr=invest == 0)
            model.add_component('dis_not_select_' + self.name, dis_not_select)
            dis_not_select.add_component('not_select_size_' + self.name,
                                         not_select_size)
            dis_not_select.add_component('not_select_inv_' + self.name,
                                         not_select_inv)

            dis_select = Disjunct()
            select_size = pyo.Constraint(expr=size >= min_size)
            select_inv = pyo.Constraint(expr=invest == size * self.unit_cost +
                                        self.fixed_cost)
            model.add_component('dis_select_' + self.name, dis_select)
            dis_select.add_component('select_size_' + self.name, select_size)
            dis_select.add_component('select_inv_' + self.name, select_inv)

            dj_size = Disjunction(expr=[dis_not_select, dis_select])
            model.add_component('disjunction_size' + self.name, dj_size)
        elif self.cost_model == 2:
            pair_nr = len(self.cost_pair)
            pair = Disjunct(pyo.RangeSet(pair_nr + 1))
            model.add_component(self.name + '_cost_pair', pair)
            pair_list = []
            for i in range(pair_nr):
                size_data = float(self.cost_pair[i].split(';')[0])
                price_data = float(self.cost_pair[i].split(';')[1])

                select_size = pyo.Constraint(expr=size == size_data)
                select_inv = pyo.Constraint(expr=invest == price_data)
                pair[i + 1].add_component(
                    self.name + 'select_size_' + str(i + 1),
                    select_size)
                pair[i + 1].add_component(
                    self.name + 'select_inv_' + str(i + 1),
                    select_inv)
                pair_list.append(pair[i + 1])

            select_size = pyo.Constraint(expr=size == 0)
            select_inv = pyo.Constraint(expr=invest == 0)
            pair[pair_nr + 1].add_component(self.name + 'select_size_' + str(0),
                                            select_size)
            pair[pair_nr + 1].add_component(self.name + 'select_inv_' + str(0),
                                            select_inv)
            pair_list.append(pair[pair_nr + 1])

            disj_size = Disjunction(expr=pair_list)
            model.add_component('disj_size_' + self.name, disj_size)

        annuity = calc_annuity(self.life, invest - city_subsidy - state_subsidy - country_subsidy,
                               self.f_inst, self.f_w, self.f_op)
        model.cons.add(annuity == annual_cost)

    def _constraint_subsidies(self, model):
        for component in self.components:
            pur_subsidy = model.find_component('pur_subsidy_' + component.name)

            pur_subsidy_list = []
            for subsidy in self.subsidy_list:
                subsidy_var = None
                if len(subsidy.components) == 1:
                    subsidy_var = model.find_component('subsidy_' + subsidy.name +
                                                       '_' + subsidy.components[0])
                else:
                    warnings.warn(subsidy.name + " has multiple subsidies for components")

                if subsidy.type == 'purchase':
                    pur_subsidy_list.append(subsidy_var)

            if len(pur_subsidy_list) > 0:
                model.cons.add(pur_subsidy == pur_subsidy)
            else:
                model.cons.add(pur_subsidy == 0)

    def constraint_sum_inputs(self, model, energy_type):
        input_flows = []
        for energy, flow in self.energy_flows['input'].items():
            if energy == energy_type:
                for item in flow:
                    input_flows.append(model.find_component(energy + '_' +
                                                            item[0] + '_' +
                                                            item[1]))
        input_energy = model.find_component('input_' + energy_type + '_' +
                                            self.name)

        # Sum up all the inputs
        for t in model.time_step:
            model.cons.add(input_energy[t] == sum(input_flow[t] for
                                                  input_flow in input_flows))

    def constraint_sum_outputs(self, model, energy_type):
        output_flows = []
        for energy, flow in self.energy_flows['output'].items():
            if energy == energy_type:
                for item in flow:
                    output_flows.append(model.find_component(energy + '_' +
                                                             item[0] + '_' +
                                                             item[1]))
        output_energy = model.find_component('output_' + energy_type + '_' +
                                             self.name)

        # Sum up all the inputs
        for t in model.time_step:
            model.cons.add(output_energy[t] == sum(output_flow[t] for
                                                   output_flow in output_flows))

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_maxpower(model)
        self._constraint_vdi2067(model)

        if len(self.subsidy_list) > 0:
            self._constraint_subsidies(model)
            for subsidy in self.subsidy_list:
                subsidy.add_cons(model)

    def add_vars(self, model):
        comp_size = pyo.Var(bounds=(self.min_size, self.max_size))
        model.add_component('size_' + self.name, comp_size)

        annual_cost = pyo.Var(bounds=(0, 10 ** 10))
        model.add_component('annual_cost_' + self.name, annual_cost)

        invest = pyo.Var(bounds=(0, 10 ** 10))
        model.add_component('invest_' + self.name, invest)

        city_subsidy = pyo.Var(bounds=(0, 10 ** 10))
        model.add_component('city_subsidy_' + self.name, city_subsidy)

        state_subsidy = pyo.Var(bounds=(0, 10 ** 10))
        model.add_component('state_subsidy_' + self.name, state_subsidy)

        country_subsidy = pyo.Var(bounds=(0, 10 ** 10))
        model.add_component('country_subsidy_' + self.name, country_subsidy)

        if self.inputs is not None:
            for energy_type in self.inputs:
                input_energy = pyo.Var(model.time_step, bounds=(0, 10 ** 10))
                model.add_component('input_' + energy_type + '_' + self.name,
                                    input_energy)

        if self.outputs is not None:
            for energy_type in self.outputs:
                output_energy = pyo.Var(model.time_step, bounds=(0, 10 ** 10))
                model.add_component('output_' + energy_type + '_' + self.name,
                                    output_energy)

        if self.other_op_cost:
            other_op_cost = pyo.Var(bounds=(0, 10 ** 10))
            model.add_component('other_op_cost_' + self.name, other_op_cost)
