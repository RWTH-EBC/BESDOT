"""
This is a test for base component, so that other specific components could
inherit its constraint for maximal capacity, energy transfer and cost
calculation.
"""

import warnings
import pyomo.environ as pyo
import scripts
import math
from scripts.curvefit import *


class BaseComponent:
    """
    The parent class for all components, like producing device, consumption.
    Except storage!

    Attributes:
    efficiency: float, energy transfer efficiency
     todo: preliminary define with float value, could be a variable
    capacity: float or pyomo variable, for energy producing
     components, this parameter means its maximum power in kW,
     for energy storage components, this parameter means its maximum
     storage capacity in kWh
    life: int, service life of the component
    cost: float, investment cost in EUR/kW, fixed value for each
     component will be defined with a function later
    """

    def __init__(self, comp_name, commodity_1, commodity_2,  min_size, max_size, current_size,
                 commodity_3=None, comp_type="BaseComponent", properties=None):
        """
        Args:
        commodity_1: str, energy input type, could be "gas","h2", "heat",
         "cold", "elec_ac", "elec_dc", "irr", "biomass"
        # todo into list,
        commodity_2: str, energy output type, could be "gas","h2", "heat",
         "cold", "elec_ac", "elec_dc", "demand"
         # todo into list
        commodity_3: str, usually not used, only when there are multiple
         energy outputs, such as CHP and fuel cell. Could be "heat",
         "elec_ac"
        comp_name: str, unique name for instance
        comp_type: str, type of component
        properties: dataframe, contains property of the component,
         like efficiency, service life, unit investment cost
        # todo: efficiency -> dict, key=(input, output), value=efficiency
        """
        self.input_energy = commodity_1
        self.output_energy = commodity_2
        self.output_energy_2 = commodity_3
        self.name = comp_name
        self.component_type = comp_type
        self.max_size = max_size
        self.min_size = min_size
        self.current_size = current_size
        self.properties = properties

        self._read_properties(properties)

    def _read_properties(self, properties):
        if 'efficiency' in properties.columns:
            self.efficiency = float(properties['efficiency'])
        else:
            if self.component_type not in ['BaseStorage', 'Inverter', 'LiionBattery', 'HotWaterStorage',
                                           'StandardPVGenerator', 'StandardPEMElectrolyzer', 'StandardPEMFuelCell',
                                           'PressureStorage']:
                warnings.warn("In the model database for " + self.component_type +
                              " lack of column for efficiency.")
        if 'service life' in properties.columns:
            self.life = int(properties['service life'])
        elif 'service_life' in properties.columns:
            self.life = int(properties['service_life'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for service life.")
        if 'cost' in properties.columns:
            self.cost_type = str(properties['cost_type'][0])
            if str(properties['cost_type'][0]) == 'constant':
                self.cost = float(properties['cost'])
            elif str(properties['cost_type'][0]) == 'piecewise':
                curve_parameter = properties['cost'][0].split(':')
                cost_list = curve_parameter[0].split(';')
                bp_list = curve_parameter[1].split(';')
                curve_parameter = [cost_list, bp_list]
                self.cost = curve_parameter
            elif str(properties['cost_type'][0]) == 'inverse_prop':
                curve_parameter = properties['cost'][0].split(';')
                self.cost = curve_parameter
            else:
                print('the cost type is', type(properties['cost']))

            # if len(properties['cost']) == 1:
            #     if isinstance(properties['cost'][0], str):
            #         curve_parameter = properties['cost'][0].split(';')
            #         self.cost = curve_parameter
            #     else:
            #         self.cost = float(properties['cost'])
            #     self.cost_type = str(properties['cost_type'][0])
            # elif len(properties['cost']) > 1:
            #     self.cost = properties['cost']
            #     self.cost_type = str(properties['cost_type'][0])
            # else:
            #     print('the cost type is', type(properties['cost']))
            #     print(properties['cost'])
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

    def _constraint_bidirectional_flows(self, model, var_dict, T, max_power):
        if self.bidirectional_flows:
            # Add linking constraints for the binary variables of bidirectional flows
            # to prevent simultaneous occurrence of bidirectional flows
            for power_pair in self.bidirectional_flows:
                for t in T:
                    # prohibit power in bidirectional flow
                    model.cons.add(pyo.quicksum(
                        var_dict[('z', flow[0] + '_to_' + flow[1])][t]
                        for flow in power_pair) <= 1)
                for flow in power_pair:
                    #
                    for t in T:
                        model.cons.add(
                            var_dict[flow][t] <= var_dict[('z', flow[0] + '_to_' + flow[1])][t]
                            * max_power
                        )

    def add_all_constr(self, model, flows, var_dict, T):
        self._constraint_conser(model, flows, var_dict, T)
        self._constraint_maxpower(model, flows, var_dict, T)
        # todo jgn: for test purpose, the constraint vdi2067 is temporarily deactivated
        self._constraint_vdi2067(model, var_dict, T)
        self._constraint_bidirectional_flows(model, var_dict, T, self.max_size)

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

    def _add_linking_variables(self, var_dict, flows, model, T):
        # if at some point we should have redundant constraints, this is not necessarily a bad thing, these constraints
        # further tighten the LP relaxation and can lead to a faster optimization. Even if the linking constraint that
        # ensures a single direction of bidirectional flows proves to be redundant in practice due to optimal solutions
        # that mind the efficiency of the component, this constraint does indeed reduce the feasible space making it not
        # only suboptimal but also impossible to have the undesired flows, thus strengthening the LP relaxation.
        # see Ruiz and Grossmann 2011
        # get bidirectional flows
        self.bidirectional_flows = self.define_bidirectional_flows(flows[self.input_energy],
                                                                   flows[self.output_energy])
        if self.bidirectional_flows:
            for power_pair in self.bidirectional_flows:
                for flow in power_pair:
                    linking_variable = ('z', flow[0] + '_to_' + flow[1])
                    if linking_variable not in var_dict:  # this linking variable hasn't been added yet
                        var_dict[linking_variable] = {}
                        for t in T:
                            var_dict[linking_variable][t] = pyo.Var(domain=pyo.Binary)
                            model.add_component(linking_variable[0] + '_' + linking_variable[1] + '_%s' % t,
                                                var_dict[linking_variable][t]) # Add binary linking variable to the model
                    else:  # this linking variable has already been added e.g. by the other component
                        self.bidirectional_flows.remove(power_pair)
                        break

    def define_bidirectional_flows(self, *flows_in_sector):
        # get input and output powers in the flow dict according to comp_name
        # remove repeated sectors
        if flows_in_sector[0] == flows_in_sector[1]:
            flows_in_sector = [flows_in_sector[0]]
        input_powers = []
        output_powers = []
        for flow in flows_in_sector:
            input_powers.extend(flow[self.name][0])
            output_powers.extend(flow[self.name][1])
        # define bidirectional flows
        bidirectional_flows = []
        for power in input_powers:
            if (power[1], power[0]) in output_powers:
                # create bidirectional flow pairs in
                bidirectional_flows.append((power, (power[1], power[0])))
        return bidirectional_flows
