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
         todo: preliminary define with float value, could be a pyomo variable
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
        self.inputs = None
        self.outputs = None

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
        if 'efficiency' in properties.columns:
            self.efficiency = float(properties['efficiency'])
        else:
            if self.component_type not in ['BaseStorage', 'Inverter', 'Battery',
                                           'HotWaterStorage', 'PV']:
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

    def _get_unit_cost(self, var_dict, model):
        # var_dict[('power', self.name)]
        unit_cost = 0
        if self.cost_type == 'constant':
            unit_cost = self.cost
        elif self.cost_type == 'piecewise':
            print(self.cost)
            cost_list = self.cost[0]  # unit cost of each step
            bp_list = self.cost[1]  # breakpoint for steps
            model.unit_cost = pyo.Var()
            for i in range(len(cost_list)):
                cost_deter = pyo.Var(within=pyo.Binary)
                model.add_component('cost_deter_' + str(i), cost_deter)
            # fixme: hard coding for quartal meeting, should not only for 2
            #  steps.
            model.cons.add(model.cost_deter_0 + model.cost_deter_1 == 1)
            model.cons.add(model.unit_cost == model.cost_deter_0 * float(
                cost_list[0]) + model.cost_deter_1 * float(cost_list[1]))
            model.cons.add(var_dict[('power', self.name)] <= float(bp_list[0]) *
                           model.cost_deter_0 + 10000 * model.cost_deter_1)
            model.cons.add(var_dict[('power', self.name)] >= float(bp_list[0]) *
                           model.cost_deter_1 + 0.0001)
            unit_cost = model.unit_cost
        elif self.cost_type == 'inverse_prop':
            unit_cost = inverse_prop_func(var_dict[('power', self.name)],
                                          float(self.cost[0]),
                                          float(self.cost[1]),
                                          float(self.cost[2]))
        else:
            print('The cost curve type', self.cost_type, 'is not found')
            print(self.cost)
            print(self.cost_type)

        return unit_cost

    def _constraint_conser(self, model, flows, var_dict, T):
        """
        This constraint shows the energy transfer of the component.
        For Producing components, the input energy is transfer to output
        energy with given efficiency.
        todo(yni): should adapt for CHP and fuel cell
        """
        # find out the component in flow dictionary according to name
        input_powers = flows[self.input_energy][self.name][0]
        output_powers = flows[self.output_energy][self.name][1]
        if not self.output_energy_2:
            output_powers_2 = flows[self.output_energy][self.name][1]

        for t in T:
            model.cons.add(pyo.quicksum(var_dict[i][t] for i in input_powers)
                           * self.efficiency ==
                           pyo.quicksum(var_dict[i][t] for i in output_powers))

    def _constraint_maxpower(self, model, flows, var_dict, T):
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

    def _constraint_vdi2067(self, model, var_dict, T):
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

    def add_all_constr(self, model, flows, var_dict, T):
        self._constraint_conser(model, flows, var_dict, T)
        self._constraint_maxpower(model, flows, var_dict, T)
        # todo jgn: for test purpose, the constraint vdi2067 is temporarily deactivated
        self._constraint_vdi2067(model, var_dict, T)

    def add_variables(self, input_profiles, plant_parameters, var_dict, flows,
                      model, T):
        # Assign the variables, which are only used in component internal,
        # for example, power of each component.
        lb_power = self.min_size
        ub_power = self.max_size
        if math.isinf(self.min_size):
            lb_power = None
        if math.isinf(self.max_size):
            ub_power = None
        var_dict[('power', self.name)] = pyo.Var(bounds=(lb_power, ub_power))
        model.add_component('power_' + self.name, var_dict[('power', self.name)])
        # todo jgn: for test purpose, the constraint vdi2067 and its variables are temporarily deactivated
        var_dict[('annual_cost', self.name)] = pyo.Var(bounds=(0, None))
        model.add_component('annual_cost_' + self.name, var_dict[('annual_cost', self.name)])
        var_dict[('invest_cost', self.name)] = pyo.Var(bounds=(0, None))
        model.add_component('invest_cost' + self.name,
                            var_dict[('invest_cost', self.name)])
        # The linking variables should be added if the bidirectional flows occur
        # around this component
        self._add_linking_variables(var_dict, flows, model, T)
