"""
Simplified Modell for internal use.
"""

import warnings
import pyomo.environ as pyo
import numpy as np
from tools.gen_heat_profile import *
from tools.gen_elec_profile import gen_elec_profile
from tools import get_all_class

module_dict = get_all_class.run()


class Building(object):
    def __init__(self, name, area, solar_area=None,
                 bld_typ='Verwaltungsgebäude',
                 annual_heat_demand=None,
                 annual_elec_demand=None):
        """
        Initialization for building.
        :param name: name of the building, should be unique
        """
        self.name = name
        self.area = area
        if solar_area is None:
            # if the information about the available area for solar of the 
            # building is not given, here using a factor of 10% of the total 
            # area to assume it.  
            self.solar_area = self.area * 0.1
        else:
            self.solar_area = solar_area
        self.building_typ = bld_typ
        # fixme (yni): The building type is in German, which is connected with
        #  the script "gen_heat_profil" and needs to be changed to English
        # todo (yni): TEK provided only the value for non-residential building.
        #  For residential building should get the data from the project TABULA.

        # Calculate the annual energy demand for heating, hot water and
        # electricity. Using TEK Tools from IWU.
        self.annual_demand = {"elec_demand": 0,
                              "heat_demand": 0,
                              "cool_demand": 0,
                              "hot_water_demand": 0,
                              "gas_demand": 0}
        if annual_heat_demand is None:
            self.add_annual_demand('heat')
        elif not isinstance(annual_heat_demand, float):
                warn_msg = 'The annual_heat_demand of ' + self.name + \
                           ' is not float, need to check.'
                warnings.warn(warn_msg)
        else:
            self.annual_demand["heat_demand"] = annual_heat_demand

        if annual_elec_demand is None:
            self.add_annual_demand('elec')
        elif not isinstance(annual_elec_demand, float):
            warn_msg = 'The annual_elec_demand of ' + self.name + \
                       ' is not float, need to check.'
            warnings.warn(warn_msg)
        else:
            self.annual_demand["elec_demand"] = annual_elec_demand

        # The gas_demand is for natural gas, the demand of hydrogen is still not
        # considered in building. The profile of heat and cool demand depends
        # on the air temperature, which is define in the Environment object.
        # So the method for generate profiles should be called in project
        # rather than in building object.
        self.demand_profile = {"elec_demand": [],
                               "heat_demand": [],
                               "cool_demand": [],
                               "hot_water_demand": [],
                               "gas_demand": []}

        # The topology of the building energy system and all available
        # components in the system, which doesn't mean the components would
        # have to be choose by optimizer.
        self.topology = None
        self.components = {}
        self.simp_matrix = None
        self.energy_flow = None
        self.heat_flows = None

    def add_annual_demand(self, energy_sector):
        """Calculate the annual heat demand according to the TEK provided
        data, the temperature profile should be given in Project"""
        demand = calc_bld_demand(self.building_typ, self.area, energy_sector)
        if energy_sector == 'heat':
            self.annual_demand["heat_demand"] = demand
        elif energy_sector == 'elec':
            self.annual_demand["elec_demand"] = demand
        else:
            warn("Other energy sector, except 'heat' and 'elec', are not "
                 "developed, so could not use the method. check again or fixe "
                 "the problem with changing this method add_annual_demand")

    def add_thermal_profile(self, energy_sector, temperature_profile, env):
        """The heat and cool demand profile could be calculated with
        temperature profile according to degree day method.
        Attention!!! The temperature profile could only provided in project
        object, so this method cannot be called in the initialization of
        building object."""
        # todo (yni): the current version is only for heat, the method could be
        #  developed for cool demand later.
        if energy_sector == 'heat':
            heat_demand_profile = gen_heat_profile(self.building_typ,
                                                   self.area,
                                                   temperature_profile)
            self.demand_profile["heat_demand"] = heat_demand_profile[
                                                 env.start_time:
                                                 env.start_time + env.time_step]
        elif energy_sector == 'cool':
            warn('Profile for cool is still not developed')
        else:
            warn_msg = 'The ' + energy_sector + ' is not allowed, check the ' \
                                                'method add_thermal_profile '

            warn(warn_msg)

    def add_elec_profile(self, year, env):
        """Generate the electricity profile with the 'Standardlastprofil'
        method. This method could only be called in the Project object,
        because the year is stored in the Environment object"""
        elec_demand_profile = gen_elec_profile(self.annual_demand[
                                                   "elec_demand"],
                                               self.building_typ,
                                               year)
        self.demand_profile["elec_demand"] = elec_demand_profile[
                                             env.start_time:
                                             env.start_time + env.time_step]

    def add_topology(self, topology):
        topo_matrix = pd.read_csv(topology)
        self.topology = topo_matrix

    def add_components(self, env):
        """Generate the components according to topology matrix and add
        all the components to the self list"""
        if self.topology is None:
            warn('No topology matrix is found in building!')
        else:
            for item in self.topology.index:
                comp_name = self.topology['comp_name'][item]
                comp_type = self.topology['comp_type'][item]
                comp_model = self.topology['model'][item]
                min_size = self.topology['min_size'][item]
                max_size = self.topology['max_size'][item]
                current_size = self.topology['current_size'][item]
                if comp_type in ['HeatPump', 'GasHeatPump']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      temp_profile=
                                                      env.temp_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['PV', 'SolarThermalCollector']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      irr_profile=
                                                      env.irr_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type == 'HeatConsumption':
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      consum_profile=
                                                      self.demand_profile[
                                                          'heat_demand'],
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type == 'ElectricalConsumption':
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      consum_profile=
                                                      self.demand_profile[
                                                          'elec_demand'],
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type == 'HotWaterConsumption':
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      consum_profile=
                                                      self.demand_profile[
                                                          'hot_water_demand'],
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type == 'ThreePortValve':
                    comp_obj = module_dict[comp_type](comp_name=comp_name)
                else:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                self.components[comp_name] = comp_obj

    def add_vars(self, model):
        """Add Pyomo variables into the ConcreteModel, which is defined in
        project object. So the model should be given in project object
        build_model.
        The following variable should be assigned:
            Energy flow from a component to another [t]: this should be define
            according to the component inputs and outputs possibility and the
            building topology. For each time step.
            Total Energy input and output of each component [t]: this should be
            assigned in each component object. For each time step.
            Component size: should be assigned in component object, for once.
        """
        # Assign the variables for the energy flows according to system
        # topology. The input energy type and output energy type could be
        # used to reduce the number of variables.
        # Simplify the matrix at first, only the topology related information
        # are left. Then search the items, which equal to 1, that means the
        # energy could flow from the index component to the column component.
        # The component pairs are stored in the dictionary energy_flow.
        simp_matrix = self.topology.drop(['comp_type', 'model', 'min_size',
                                          'max_size', 'current_size'], axis=1)
        simp_matrix.set_index(['comp_name'], inplace=True)
        energy_flow = {}
        heat_flows = {}
        for index, row in simp_matrix.iteritems():
            # search for Nan value and the mass flow in topology matrix, the
            # unit is kg/h.
            # print(row[row.isnull()].index.tolist())
            if len(row[row > 0].index.tolist() +
                   row[row.isnull()].index.tolist()) > 0:
                for input_comp in row[row > 0].index.tolist() + \
                                  row[row.isnull()].index.tolist():
                    energy_flow[(input_comp, index)] = pyo.Var(
                        model.time_step, bounds=(0, None))
                    model.add_component(input_comp + '_' + index,
                                        energy_flow[(input_comp, index)])

                    # Check, if heat is the output of the component,
                    # input should not be considered. The reason for it is
                    # avoiding duplicate definition, since in building
                    # level the input of one component is the output of
                    # another component.
                    # todo (yni): Check, if need both outputs and inputs and
                    #  if the following method could cause duplicate variable.
                    if 'heat' in self.components[input_comp].outputs or \
                            'heat' in self.components[input_comp].inputs:
                        # Check if the component has the attribution of
                        # 'flows', which shows if the model contains
                        # temperature variables.
                        # todo (yni): check, wenn the following command could
                        #  be required.
                        # if hasattr(self.components[input_comp],
                        #            'heat_flows_in'):
                        heat_flows[(input_comp, index)] = {}
                        heat_flows[(index, input_comp)] = {}
                        # mass flow from component 'input_comp' to
                        # component 'index'.
                        heat_flows[(input_comp, index)]['mass'] = \
                            pyo.Var(model.time_step, bounds=(0, None))
                        model.add_component(input_comp + '_' + index +
                                            '_' + 'mass', heat_flows[(
                            input_comp, index)]['mass'])
                        # mass flow from component 'index' to
                        # component 'index'.
                        heat_flows[(index, input_comp)]['mass'] = \
                            pyo.Var(model.time_step, bounds=(0, None))
                        model.add_component(index + '_' + input_comp +
                                            '_' + 'mass', heat_flows[(
                            index, input_comp)]['mass'])
                        # temperature of heat flow from component
                        # 'input_comp' to component 'index'.
                        heat_flows[(input_comp, index)]['temp'] = \
                            pyo.Var(model.time_step, bounds=(0, None))
                        model.add_component(input_comp + '_' + index +
                                            '_' + 'temp', heat_flows[(
                            input_comp, index)]['temp'])
                        # temperature of heat flow from component
                        # 'index' to component 'input_comp'.
                        heat_flows[(index, input_comp)]['temp'] = \
                            pyo.Var(model.time_step, bounds=(0, None))
                        model.add_component(index + '_' + input_comp +
                                            '_' + 'temp', heat_flows[(
                            index, input_comp)]['temp'])

        # Save the simplified matrix and energy flow for energy balance
        self.simp_matrix = simp_matrix
        self.energy_flow = energy_flow
        self.heat_flows = heat_flows

        total_annual_cost = pyo.Var(bounds=(0, None))
        total_operation_cost = pyo.Var(bounds=(0, None))
        # Attention. The building name should be unique, not same as the comp
        # or project or other buildings.
        model.add_component('annual_cost_' + self.name, total_annual_cost)
        model.add_component('operation_cost_' + self.name, total_operation_cost)

        for comp in self.components:
            self.components[comp].add_vars(model)

    def add_cons(self, model, env):
        self._constraint_energy_balance(model)
        self._constraint_mass_balance(model)
        # todo (yni): Attention in the optimization for operation cost should
        #  comment constrain for solar area. This should be done automated.
        # self._constraint_solar_area(model)
        self._constraint_total_cost(model, env)
        self._constraint_operation_cost(model, env)
        for comp in self.components:
            if hasattr(self.components[comp], 'heat_flows_in'):
                if isinstance(self.components[comp].heat_flows_in, list):
                    self.components[comp].add_heat_flows_in(self.energy_flow)
            if hasattr(self.components[comp], 'heat_flows_out'):
                if isinstance(self.components[comp].heat_flows_out, list):
                    self.components[comp].add_heat_flows_out(self.energy_flow)
            self.components[comp].add_cons(model)

    def _constraint_energy_balance(self, model):
        """According to the energy system topology, the sum of energy flow
        into a component should be equal to the component inputs. The sum of
        energy flow out of a component to other components should be equal to
        component outputs.
        Attention! If a component has more than 1 inputs or outputs, should
        distinguish between different energy carriers"""
        # todo (yni): the method for more than 1 inputs or outputs should be
        #  validiert.

        # Constraints for the inputs
        for index, row in self.simp_matrix.iteritems():
            if self.components[index].inputs is not None:
                for energy_type in self.components[index].inputs:
                    if len(row[row > 0].index.tolist() +
                           row[row.isnull()].index.tolist()) > 0:
                        input_components = row[row > 0].index.tolist() + \
                                           row[row.isnull()].index.tolist()
                        input_energy = model.find_component('input_' +
                                                            energy_type + '_' +
                                                            index)
                        for t in model.time_step:
                            model.cons.add(input_energy[t] == sum(
                                self.energy_flow[(input_comp, index)][t] for
                                input_comp in input_components))

        # Constraints for the outputs
        for index, row in self.simp_matrix.iterrows():
            if self.components[index].outputs is not None:
                for energy_type in self.components[index].outputs:
                    if len(row[row > 0].index.tolist() +
                           row[row.isnull()].index.tolist()) > 0:
                        output_components = row[row > 0].index.tolist() + \
                                            row[row.isnull()].index.tolist()
                        output_energy = model.find_component('output_' +
                                                             energy_type + '_' +
                                                             index)
                        for t in model.time_step:
                            model.cons.add(output_energy[t] == sum(
                                self.energy_flow[(index, output_comp)][t] for
                                output_comp in output_components))

    def _constraint_solar_area(self, model):
        """The total available solar area should be shared by PV and solar
        thermal collector."""
        solar_area_var_list = []
        for component in self.components:
            if isinstance(self.components[component], module_dict['PV']):
                solar_area_var_list.append(model.find_component('solar_area_' +
                                                                component))
            elif isinstance(self.components[component],
                            module_dict['SolarThermalCollector']):
                solar_area_var_list.append(model.find_component('solar_area_' +
                                                                component))
        model.cons.add(sum(item for item in solar_area_var_list) <=
                       self.solar_area)

    def _constraint_mass_balance(self, model):
        # Constraint for the mass flow, based on the assumption, that the
        # mass flow in each circulation should be same.
        # todo (yni): seems not necessary, because the mass flow balance are
        #  defined in each component? Decide it later.
        # It seems that, adding constraint in building could reduce the total
        # constraints number.
        if self.heat_flows is not None:
            for heat_flow in self.heat_flows:
                flow_1 = model.find_component(heat_flow[0] + '_' + heat_flow[1]
                                              + '_' + 'mass')
                flow_2 = model.find_component(heat_flow[1] + '_' + heat_flow[0]
                                              + '_' + 'mass')
                for t in model.time_step:
                    if self.simp_matrix[heat_flow[0]][heat_flow[1]] > 0:
                        # todo (yni): take care of the situation for variable
                        #  mass flow.
                        model.cons.add(flow_1[t] == flow_2[t])
                        model.cons.add(flow_1[t] == self.simp_matrix[
                            heat_flow[0]][heat_flow[1]])
                    elif np.isnan(self.simp_matrix[heat_flow[0]][heat_flow[1]]):
                        model.cons.add(flow_1[t] == flow_2[t])
                        # print(flow_1[t])
                        # print(flow_2[t])

    def _constraint_total_cost(self, model, env):
        """Calculate the total annual cost for the building energy system."""
        bld_annual_cost = model.find_component('annual_cost_' + self.name)
        buy_elec = [0] * 8761
        sell_elec = [0] * 8761
        buy_gas = [0] * 8761
        buy_heat = [0] * 8761

        comp_cost_list = []
        for comp in self.components:
            comp_cost_list.append(model.find_component('annual_cost_' + comp))
            if isinstance(self.components[comp],
                          module_dict['ElectricityGrid']):
                buy_elec = model.find_component('output_elec_' + comp)
                sell_elec = model.find_component('input_elec_' + comp)
            elif isinstance(self.components[comp], module_dict['GasGrid']):
                buy_gas = model.find_component('output_gas_' + comp)
            elif isinstance(self.components[comp], module_dict['HeatGrid']):
                buy_heat = model.find_component('output_heat_' + comp)

        # model.cons.add(bld_annual_cost == sum(buy_elec[t] * env.elec_price
        #                                       for t in model.time_step))
        model.cons.add(bld_annual_cost == sum(buy_elec[t] * env.elec_price +
                                              buy_gas[t] * env.gas_price +
                                              buy_heat[t] *
                                              env.heat_price - sell_elec[
                                                  t] * env.elec_feed_price
                                              for t in model.time_step) +
                       sum(item for item in comp_cost_list))

    def _constraint_operation_cost(self, model, env):
        """Calculate the total operation cost for the building energy system."""
        bld_operation_cost = model.find_component('operation_cost_' + self.name)
        buy_elec = [0] * 8761
        sell_elec = [0] * 8761
        buy_gas = [0] * 8761
        buy_heat = [0] * 8761

        comp_cost_list = []
        for comp in self.components:
            comp_cost_list.append(model.find_component('annual_cost_' + comp))
            if isinstance(self.components[comp],
                          module_dict['ElectricityGrid']):
                buy_elec = model.find_component('output_elec_' + comp)
                sell_elec = model.find_component('input_elec_' + comp)
            elif isinstance(self.components[comp], module_dict['GasGrid']):
                buy_gas = model.find_component('output_gas_' + comp)
            elif isinstance(self.components[comp], module_dict['HeatGrid']):
                buy_heat = model.find_component('output_heat_' + comp)

        model.cons.add(bld_operation_cost == sum(buy_elec[t] * env.elec_price +
                                                 buy_gas[t] * env.gas_price +
                                                 buy_heat[t] *
                                                 env.heat_price - sell_elec[
                                                  t] * env.elec_feed_price
                                                 for t in model.time_step))
