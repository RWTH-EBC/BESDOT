"""
The parent class for all energy components.
In this class except the basic attributes will be defined, the methods for
building pyomo model are also developed.
"""

import os
import warnings
import pandas as pd
import pyomo.environ as pyo
from tools.calc_annuity_vdi2067 import calc_annuity

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Component(object):
    """
    Attributes:
    inputs: list, the energy carrier or energy sector for input
    outputs: list, the energy carrier or energy sector for output
    properties: dataframe, the properties of a component object,
    the following items should be included.
        efficiency: float, energy transfer efficiency
        capacity: float or pyomo variable, for energy producing
         components, this parameter means its maximum power in kW,
         for energy storage components, this parameter means its maximum
         storage capacity in kWh
        life: int, service life of the component
        cost: float, investment cost in EUR/kW, fixed value for each
         component will be defined with a function later
    """

    def __init__(self, comp_name, comp_type="Component", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        """
        """
        self.name = comp_name
        self.component_type = comp_type
        if not hasattr(self, 'inputs'):
            self.inputs = []
        if not hasattr(self, 'outputs'):
            self.outputs = []
        self.efficiency = {'elec': None,
                           'heat': None,
                           'cool': None}

        properties = self.get_properties(comp_model)
        self._read_properties(properties)
        self.min_size = min_size
        self.max_size = max_size
        self.current_size = current_size

        self.energy_flows = {'input': {},
                             'output': {}}

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
                self.efficiency[self.outputs[0]] = float(properties[
                                                             'efficiency'])
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
        if 'cost' in properties.columns:
            self.cost = float(properties['cost'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for cost.")
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

    def add_energy_flows(self, io, energy_type, energy_flow):
        if io in ['input', 'output']:
            if energy_type not in self.energy_flows[io].keys():
                self.energy_flows[io][energy_type] = []
            self.energy_flows[io][energy_type].append(energy_flow)
        else:
            warnings.warn("io of the function add_energy_flow only allowed "
                          "for 'input' or 'output'.")

    def _constraint_conver(self, model):
        """
        This constraint shows the energy conversion of the component.
        """
        # todo: the component with more than 1 inputs is not developed,
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
        """
        The energy flow at each time step cannot be greater than its capacity.
        Here output energy is used.
        todo(yni): capacity of some device are defined with input power,
         some are defined with output power. need to check later. In first
         version is only input power considered. Check it for heat pump and CHP!
        """
        if self.outputs is not None:
            size = model.find_component('size_' + self.name)
            if len(self.outputs) == 1:
                output_powers = model.find_component('output_' +
                                                     self.outputs[0] + '_' +
                                                     self.name)
            else:
                if 'elec' in self.outputs:
                    # The size of CHP and fuel cell are define with electric
                    # capacity
                    output_powers = model.find_component('output_elec_' +
                                                         self.name)
                else:
                    output_powers = model.find_component('output_' +
                                                         self.outputs[0] + '_' +
                                                         self.name)

            for t in model.time_step:
                model.cons.add(output_powers[t] <= size)

    def _constraint_vdi2067(self, model):
        """
        t: observation period in years
        r: price change factor (not really relevant since we have n=0)
        q: interest factor
        n: number of replacements
        """
        size = model.find_component('size_' + self.name)
        annual_cost = model.find_component('annual_cost_' + self.name)
        invest = model.find_component('invest_' + self.name)

        model.cons.add(size * self.cost == invest)
        annuity = calc_annuity(self.life, invest, self.f_inst, self.f_w,
                               self.f_op)
        model.cons.add(annuity == annual_cost)

    def constraint_sum_inputs(self, model, energy_type, energy_flows):
        """
        This function used to be in class Building. Some spacial components have
        more than 1 input type, which could not be seen as input. The function
        should be rewritten in those spacial components.
        Args:
            model: pyomo model object
            other_comp: pandas Series, taken from building topology
            energy_type: modeled energy type in case of more than 1 input type
            energy_flows: the energy flows from building object, dict
            comp_obj: the component objects in building, might be used by the
                spacial components, dict
        Returns: None
        """
        # Search connected component from other_comp
        # input_components = other_comp[other_comp > 0].index.tolist() + \
        #                    other_comp[other_comp.isnull()].index.tolist()
        # input_energy = model.find_component('input_' + energy_type + '_' +
        #                                     self.name)
        # # Sum up all the inputs
        # for t in model.time_step:
        #     model.cons.add(input_energy[t] == sum(
        #         energy_flow[(input_comp, self.name)][t] for input_comp in
        #         input_components))
        input_flows = []
        for flow in energy_flows[energy_type]:
            if flow[1] == self.name:
                input_flows.append(flow)
        input_energy = model.find_component('input_' + energy_type + '_' +
                                            self.name)

        print(self.name)
        # Sum up all the inputs
        for t in model.time_step:
            model.cons.add(input_energy[t] == sum(
                energy_flows[energy_type][input_flow][t] for input_flow in input_flows))

    def constraint_sum_outputs(self, model, energy_type, energy_flows):
        """
        Almost same as constraint_energy_inputs.
        Args:
            model: pyomo model object
            other_comp: pandas Series, taken from building topology
            energy_type: modeled energy type in case of more than 1 input type
            energy_flows: the energy flows from building object, dict
        Returns: None
        """
        # output_components = other_comp[other_comp > 0].index.tolist() + \
        #                     other_comp[other_comp.isnull()].index.tolist()
        # output_energy = model.find_component('output_' + energy_type + '_' +
        #                                      self.name)
        # for t in model.time_step:
        #     model.cons.add(output_energy[t] == sum(
        #         energy_flow[(self.name, output_comp)][t] for
        #         output_comp in output_components))

        output_flows = []
        for flow in energy_flows[energy_type]:
            if flow[0] == self.name:
                output_flows.append(flow)
        output_energy = model.find_component('output_' + energy_type + '_' +
                                             self.name)
        # Sum up all the inputs
        for t in model.time_step:
            model.cons.add(output_energy[t] == sum(
                energy_flows[energy_type][output_flow][t] for output_flow in output_flows))

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_maxpower(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        """
        Add Pyomo variables into the ConcreteModel
        The following variable should be assigned:
            Component size: should be assigned in component object, for once.
            Annual cost: for once
            Investigation: for once
            Total Energy input and output of each component [t]: this should be
            assigned in each component object. For each time step.
        """

        comp_size = pyo.Var(bounds=(self.min_size, self.max_size))
        model.add_component('size_' + self.name, comp_size)

        annual_cost = pyo.Var(bounds=(0, None))
        model.add_component('annual_cost_' + self.name, annual_cost)

        invest = pyo.Var(bounds=(0, None))
        model.add_component('invest_' + self.name, invest)

        if self.inputs is not None:
            for energy_type in self.inputs:
                input_energy = pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                model.add_component('input_' + energy_type + '_' + self.name,
                                    input_energy)

        if self.outputs is not None:
            for energy_type in self.outputs:
                output_energy = pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                model.add_component('output_' + energy_type + '_' + self.name,
                                    output_energy)
