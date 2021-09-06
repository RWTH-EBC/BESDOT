import pyomo.environ as pyo
from scripts import calc_annuity_vdi2067
from datetime import timedelta


class EnergyManagementSystem:
    def __init__(self, prosumer_name, prosumer_configuration, strategy, plant_parameters, flows, components, properties):
        self.name = 'EMS_' + prosumer_name
        self.__strategy = strategy
        self.__plant_parameters = plant_parameters
        self.__flows = flows
        # self.__hydrog_flows = flows['hydrogen']
        self.__components = components
        self.__properties = properties
        self.__configuration_dict = prosumer_configuration
        self.__model_resolution = plant_parameters['t_step']

        # for configuration in prosumer_configuration:
        #     if configuration in self.__configuration_dict:
        #         self.__configuration_dict[configuration] = prosumer_configuration[configuration]
        #     else:
        #         print('The input:', configuration, 'is not a valid configuration')


    @staticmethod
    def __calculate_annuity_factor(n, i):
        # calculates annuity factor
        anf = (((1+i)**n)*i)/((1+i)**n-1)
        return anf

    @staticmethod
    def __calculate_net_present_value(n, i):
        # calculates factor for npv in the case of constant yearly opex (RBF)
        npvf = ((1+i)**n-1)/(((1+i)**n)*i)
        return npvf

    def __calculate_npv_invest(self, n, inv, fix_cost):
        # ToDo: @yi implement variable investment costs here, reinvestment, etc
        # here we use the n given by the component dataset rather than the one in self because of components that need
        # to be replaced
        npv_inv = inv*(1 + fix_cost * self.__calculate_net_present_value(n, self.__configuration_dict['yearly_interest']))
        return npv_inv

    def __add_objective_variable_operation_costs(self, model, var_dict, time_steps):
        """
        related components:
        1. Supply networks: "StandardACGrid", "StandardGasGrid", (not implemented yet) "DCGrid", "HeatNetwork",
        "CoolingNetwork", "HydrogenNetwork" and
        2. CO2-emission-related components: "Gasboiler" (CO2 costs not implemented yet)
        """
        grid_inputs = []
        grid_outputs = []
        gas_grid_outputs = []

        for component, comp_type in self.__components:
            if comp_type == 'StandardACGrid':
                grid_inputs += self.__flows['electricity'][component][0]
                grid_outputs += self.__flows['electricity'][component][1]
            if comp_type == 'StandardGasGrid':
                gas_grid_outputs += self.__flows['gas'][component][1]

        model.f1 = pyo.Var()

        # todo jgn: check the unit of value in var_dict: [kW] * [h] * [Euro/kWh]
        model.C_f1 = pyo.Constraint(expr=model.f1 ==
            - pyo.quicksum(var_dict[i][t] * self.__configuration_dict['elec_price'] * self.__model_resolution for i in grid_outputs for t in time_steps)  # predicted_parameters['prices'][t]
            - pyo.quicksum(var_dict[i][t] * self.__configuration_dict['gas_price'] * self.__model_resolution for i in gas_grid_outputs for t in time_steps)
            + pyo.quicksum(var_dict[i][t] * self.__configuration_dict['injection_price'] * self.__model_resolution for i in grid_inputs for t in time_steps))

        model.O_f1 = pyo.Objective(expr=model.f1, sense=pyo.maximize)

    def __add_objective_own_consumption(self, model, var_dict, time_steps):
        """
        related components:
        1. Supply networks: "StandardACGrid", "StandardGasGrid", (not implemented yet) "DCGrid", "HeatNetwork",
        "CoolingNetwork", "HydrogenNetwork" and
        2. Consumption components: "StandardElectricalConsumption", (not implemented yet) "HeatConsumption",
        "CoolingConsumption"
        """
        # Todo jgn: rethink about the definition of own consumption, where should the loss go?
        #  The implementation is hard coded now.
        # Maximize own consumption: max (inv_elec_cns - elec bezug - gas bezug)
        gas_grid_outputs = []
        grid_outputs = []
        inv_elec_cns = []

        for component, comp_type in self.__components:
            if comp_type == 'StandardACGrid':
                grid_outputs += self.__flows['electricity'][component][1]
            elif comp_type == 'StandardGasGrid':
                gas_grid_outputs += self.__flows['gas'][component][1]
            elif comp_type == 'StandardElectricalConsumption':
                for flow in self.__flows['electricity'][component][0]:
                    if (flow[0], 'BasicInverter') in self.__components:
                        inv_elec_cns.append(flow)

        model.f1 = pyo.Var()

        model.C_f1 = pyo.Constraint(expr=model.f1 == pyo.quicksum(var_dict[i][t] * self.__model_resolution for i in inv_elec_cns for t in time_steps))
            # pyo.quicksum(var_dict[i][t] for i in grid_outputs) -
            # pyo.quicksum(var_dict[i][t] for i in gas_grid_outputs)  # - grid inputs???
            # -pyo.quicksum(var_dict[i][t] for i in grid_inputs)
            #)

        model.O_f1 = pyo.Objective(expr=model.f1, sense=pyo.maximize)

    def __add_objective_annuity_new(self, model, var_dict, time_steps):
        """
        related components: all components that are costs (capital, demand, and operation-related) related
        """
        # determine components, that are related to demand costs (electricity, heat, gas, cooling, etc.)
        elec_grid_inputs = []
        elec_grid_outputs = []
        gas_grid_inputs = []
        gas_grid_outputs = []
        heat_grid_inputs = []
        heat_grid_outputs = []
        cooling_grid_inputs = []
        cooling_grid_outputs = []

        for component, comp_type in self.__components:
            if comp_type == 'StandardACGrid':
                elec_grid_inputs += self.__flows['electricity'][component][0]
                elec_grid_outputs += self.__flows['electricity'][component][1]
            if comp_type == 'StandardGasGrid':
                gas_grid_inputs += self.__flows['gas'][component][0]
                gas_grid_outputs += self.__flows['gas'][component][1]
            if comp_type == 'StandardHeatGrid':
                heat_grid_inputs += self.__flows['heat'][component][0]
                heat_grid_outputs += self.__flows['heat'][component][1]
            if comp_type == 'StandardCoolingGrid':
                cooling_grid_inputs += self.__flows['cooling'][component][0]
                cooling_grid_outputs += self.__flows['cooling'][component][1]

        # capital related costs and operating related costs
        annual_costs = []
        for each_var in var_dict:
            if each_var[0] == 'annual_cost':
                annual_costs.append(each_var)

        # net present value factor (PREISDYNAMISCHER Barwertfaktor) and annuity factor (Annuitätsfaktor)
        # t = (time_steps[-1] - time_steps[0] + timedelta(hours=1)) / timedelta(days=365)
        dynamic_cash_value = calc_annuity_vdi2067.dynamic_cash_value(self.__configuration_dict['planning_horizon'], r=1.03)
        annuity_factor = calc_annuity_vdi2067.annuity_factor(self.__configuration_dict['planning_horizon'])

        # The factor that convert the simulation to ONE year
        annual_factor = timedelta(days=365)/(time_steps[-1] - time_steps[0] + timedelta(hours=1))

        # add objective function
        model.f1 = pyo.Var()
        model.C_f1 = pyo.Constraint(expr=model.f1 ==
                                    - pyo.quicksum(var_dict[i] for i in annual_costs)
                                    - (pyo.quicksum(var_dict[elec_output][t] * self.__configuration_dict['elec_price'] for elec_output in elec_grid_outputs for t in time_steps)
                                       + pyo.quicksum(var_dict[gas_output][t] * self.__configuration_dict['gas_price'] for gas_output in gas_grid_outputs for t in time_steps)
                                       + pyo.quicksum(var_dict[heat_output][t] * self.__configuration_dict['heat_price'] for heat_output in heat_grid_outputs for t in time_steps)
                                       + pyo.quicksum(var_dict[cooling_output][t] * self.__configuration_dict['cooling_price'] for cooling_output in cooling_grid_outputs for t in time_steps)
                                       - pyo.quicksum(var_dict[elec_input][t] * self.__configuration_dict['injection_price'] for elec_input in elec_grid_inputs for t in time_steps)
                                       - pyo.quicksum(var_dict[gas_input][t] * self.__configuration_dict['injection_price_gas'] for gas_input in gas_grid_inputs for t in time_steps)
                                       - pyo.quicksum(var_dict[heat_input][t] * self.__configuration_dict['injection_price_heat'] for heat_input in heat_grid_inputs for t in time_steps)
                                       - pyo.quicksum(var_dict[cooling_input][t] * self.__configuration_dict['injection_price_cooling'] for cooling_input in cooling_grid_inputs for t in time_steps))
                                    * self.__model_resolution * annual_factor * dynamic_cash_value * annuity_factor)
        model.O_f1 = pyo.Objective(expr=model.f1, sense=pyo.maximize)

    def __add_objective_annuity(self, model, var_dict, time_steps):
        """
        related components:
        all components
        """
        grid_inputs = []
        grid_outputs = []
        gas_grid_outputs = []

        for component, comp_type in self.__components:
            if comp_type == 'StandardACGrid':
                grid_inputs += self.__flows['electricity'][component][0]
                grid_outputs += self.__flows['electricity'][component][1]
            if comp_type == 'StandardGasGrid':
                gas_grid_outputs += self.__flows['gas'][component][1]

        dim_components = []
        # add to list components whose size can be optimized (if they have min and max size entries in matrix)
        # ToDo @mce: only consider components that will be optimzed i.e. min_size different than max_size
        #  Annuity of Investment of the other components can be added afterwards since it's a fixed number
        #  New parameter in matrix: current_size <= min_size -> nicht bestehend, bauen, current_size: not binary!!
        for component, comp_type in self.__components:
            if 'min_size' and 'max_size' in self.__plant_parameters[(component, comp_type)]:
                dim_components.append((component, float(self.__properties[component]['service_life']),
                                       float(self.__properties[component]['inv_cost']),
                                       float(self.__properties[component]['fix_cost_factor'])))

        # ToDo: check that objective value is equal to actual value on excel
        model.f1 = pyo.Var()
        print(dim_components, [self.__calculate_npv_invest(j, k, l)*self.__calculate_annuity_factor(self.__configuration_dict['planning_horizon'], self.__configuration_dict['yearly_interest']) for i, j, k, l in dim_components], self.__calculate_net_present_value(self.__configuration_dict['planning_horizon'], self.__configuration_dict['yearly_interest']))
        model.C_f1 = pyo.Constraint(expr=model.f1 ==
            - pyo.quicksum(var_dict[('size', i)] * self.__calculate_npv_invest(j, k, l) for i, j, k, l in dim_components) * self.__calculate_annuity_factor(self.__configuration_dict['planning_horizon'], self.__configuration_dict['yearly_interest']) +
            - pyo.quicksum(var_dict[i][t] * self.__configuration_dict['elec_price'] * self.__model_resolution for i in grid_outputs for t in time_steps) * self.__calculate_net_present_value(self.__configuration_dict['planning_horizon'], self.__configuration_dict['yearly_interest']) * self.__calculate_annuity_factor(self.__configuration_dict['planning_horizon'], self.__configuration_dict['yearly_interest']) #predicted_parameters['prices'][t]
            - pyo.quicksum(var_dict[i][t] * self.__configuration_dict['gas_price'] * self.__model_resolution for i in gas_grid_outputs for t in time_steps) * self.__calculate_net_present_value(self.__configuration_dict['planning_horizon'], self.__configuration_dict['yearly_interest']) * self.__calculate_annuity_factor(self.__configuration_dict['planning_horizon'], self.__configuration_dict['yearly_interest'])
            + pyo.quicksum(var_dict[i][t] * self.__configuration_dict['injection_price'] * self.__model_resolution for i in grid_inputs for t in time_steps) * self.__calculate_net_present_value(self.__configuration_dict['planning_horizon'], self.__configuration_dict['yearly_interest']) * self.__calculate_annuity_factor(self.__configuration_dict['planning_horizon'], self.__configuration_dict['yearly_interest']))
            #for t in time_steps))

        model.O_f1 = pyo.Objective(expr=model.f1, sense=pyo.maximize)

    def __add_objective_co2(self, model, var_dict, time_steps):
        """
        related components are:
        1. Supply networks
        2. CO2-emission-related components (?)
        """
        gas_grid_outputs = []
        grid_outputs = []

        for component, comp_type in self.__components:
            if comp_type == 'StandardACGrid':
                grid_outputs += self.__flows['electricity'][component][1]
            if comp_type == 'StandardGasGrid':
                gas_grid_outputs += self.__flows['gas'][component][1]

        model.f2 = pyo.Var()
        # https://www.umweltbundesamt.de/presse/pressemitteilungen/bilanz-2019-co2-emissionen-pro-kilowattstunde-strom

        model.C_f2 = pyo.Constraint(expr=model.f2 ==
            -pyo.quicksum(var_dict[i][t] * self.__configuration_dict['elec_emission'] * self.__model_resolution for i in grid_outputs for t in time_steps)
            -pyo.quicksum(var_dict[i][t] * self.__configuration_dict['gas_emission'] * self.__model_resolution for i in gas_grid_outputs for t in time_steps))
        model.O_f2 = pyo.Objective(expr=model.f2, sense=pyo.maximize)

    def _constraint_max_injection(self, model, var_dict, time_steps):

        grid_list = []
        pv_list = []
        input_powers = []

        for component, comp_type in self.__components:
            if comp_type == 'BasicPVGenerator' or comp_type == 'StandardPVGenerator':
                pv_list.append(component)
            elif comp_type == 'StandardACGrid':
                grid_list.append(component)

        for grid in grid_list:
            # find out the component in flow dictionary according to name
            input_powers += (self.__flows['electricity'][grid][0])

        # Add power flow constraints if pv generator and grid feed-in exists
        if pv_list and input_powers:
            for t in time_steps:
                model.cons.add(
                    pyo.quicksum(var_dict[i][t] for i in input_powers) <= pyo.quicksum(var_dict[('power', i)] for i in pv_list)
                    * self.__configuration_dict['injection/pvpeak'])
            # name=grid + '_max_injection_' + str(t)
            # no names for constraints in pyomo, may be solved with a dictionary approach like for the variables,
            # see if it's worth it

    def implement_strategy(self, model, var_dict, time_steps):
        for strategy in self.__strategy:
            if strategy == 'variable_operation_costs':
                self.__add_objective_variable_operation_costs(model, var_dict, time_steps)
            elif strategy == 'own_consumption':
                self.__add_objective_own_consumption(model, var_dict, time_steps)
            elif strategy == 'annuity':
                # self.__add_objective_annuity(model, var_dict, time_steps)
                self.__add_objective_annuity_new(model, var_dict, time_steps)
            elif strategy == 'co2':
                self.__add_objective_co2(model, var_dict, time_steps)
        if self.__configuration_dict['injection/pvpeak'] is not None:
            self._constraint_max_injection(model, var_dict, time_steps)
