"""
The parent class for all energy components.
In this class except the basic attributes will be defined, the methods for
building pyomo model are also developed.
"""

import os
import warnings
import pandas as pd
import pyomo.environ as pyo


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

    def __init__(self, comp_name, comp_type="Component", comp_model=None):
        """
        """
        self.name = comp_name
        self.component_type = comp_type
        if not hasattr(self, 'inputs'):
            self.inputs = None
        if not hasattr(self, 'outputs'):
            self.outputs = None
        self.efficiency = {'elec': None,
                           'heat': None,
                           'cool': None}

        properties = self.get_properties(comp_model)
        self._read_properties(properties)

    def get_properties(self, model):
        model_property_file = os.path.join(base_path, 'data',
                                           'component_database',
                                           self.component_type,
                                           model + '.csv')
        properties = pd.read_csv(model_property_file)
        return properties

    def _read_properties(self, properties):
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
                print(self.name)
                model.cons.add(output_energy[t] == input_energy[t] *
                               self.efficiency[output])

    def _constraint_maxpower(self, model):
        """
        The power at each time step cannot be greater than the capacity.
        todo(yni): capacity of some device are defined with input power,
         some are defined with output power. need to check later. In first
         version is only input power considered.
        """
        # find out the component in flow dictionary according to name
        input_powers = flows[self.input_energy][self.name][0]
        output_powers = flows[self.output_energy][self.name][1]
        if not input_powers:  # if input_powers list is empty, use output_powers
            for t in T:
                model.cons.add(pyo.quicksum(var_dict[i][t] for i in output_powers)
                               <= var_dict[('power', self.name)])
        else:
            for t in T:
                model.cons.add(pyo.quicksum(var_dict[i][t] for i in input_powers)
                               <= var_dict[('power', self.name)])

    def _constraint_vdi2067(self, model):
        """
        t: observation period in years
        r: price change factor (not really relevant since we have n=0)
        q: interest factor
        n: number of replacements
        """
        unit_cost = self._get_unit_cost(var_dict, model)
        model.cons.add(var_dict[('power', self.name)] * unit_cost ==
                       var_dict[('invest_cost', self.name)])
        annual_cost = scripts.calc_annuity_vdi2067.run(T, self.life, unit_cost,
                                                       var_dict[('invest_cost', self.name)],
                                                       self.f_inst, self.f_w,
                                                       self.f_op,
                                                       model)
        model.cons.add(var_dict[('annual_cost', self.name)] == annual_cost)

    def add_all_constr(self, model):
        self._constraint_conver(model)
        self._constraint_maxpower(model, flows, var_dict, T)
        # todo jgn: for test purpose, the constraint vdi2067 is temporarily deactivated
        self._constraint_vdi2067(model, var_dict, T)

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

        comp_size = pyo.Var(bounds=(0, None))
        model.add_component('size_' + self.name, comp_size)

        annual_cost = pyo.Var(bounds=(0, None))
        model.add_component('annual_cost_' + self.name, annual_cost)

        invest = pyo.Var(bounds=(0, None))
        model.add_component('invest_' + self.name, invest)

        if self.inputs is not None:
            for energy_type in self.inputs:
                input_energy = pyo.Var(model.time_step, bounds=(0, None))
                model.add_component('input_' + energy_type + '_' + self.name,
                                    input_energy)

        if self.outputs is not None:
            for energy_type in self.outputs:
                output_energy = pyo.Var(model.time_step, bounds=(0, None))
                model.add_component('output_' + energy_type + '_' + self.name,
                                    output_energy)
