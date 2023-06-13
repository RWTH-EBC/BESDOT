"""
Simplified Modell for internal use.
"""

import warnings
import pyomo.environ as pyo
import numpy as np
import pandas as pd

from scripts.components.Storage import Storage
from scripts.subsidies.EEG import EEG
from utils.gen_heat_profile import *
from utils.gen_elec_profile import gen_elec_profile
from utils import get_all_class
from utils.gen_hot_water_profile import gen_hot_water_profile

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
        # electricity. Using TEK utils from IWU.
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
        self.energy_flows = {"elec": {},
                             "heat": {},
                             "cool": {},
                             "gas": {}}
        self.heat_flows = {}
        self.subsidy_list = []

        self.bilevel = False

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

    def add_thermal_profile(self, energy_sector, env):
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
                                                   env.temp_profile_whole,
                                                   env.year)
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

    def add_hot_water_profile(self, env):
        hot_water_demand_profile = gen_hot_water_profile(self.building_typ,
                                                         self.area)
        self.demand_profile["hot_water_demand"] = hot_water_demand_profile[
                                                  env.start_time:
                                                  env.start_time + env.time_step]

    def export_demand_profile(self, dir_path):
        """export demand profiles into csv file, the path of target folder
        need to be given."""
        csv_path = os.path.join(dir_path, self.name + '.csv')

        steps = max(len(self.demand_profile['elec_demand']),
                    len(self.demand_profile['heat_demand']),
                    len(self.demand_profile['cool_demand']),
                    len(self.demand_profile['hot_water_demand']),
                    len(self.demand_profile['gas_demand']))
        for k, v in self.demand_profile.items():
            if len(v) != steps and len(v) != 0:
                warn('The ' + k + 'has different time steps')
            elif len(v) == 0:
                self.demand_profile[k] = [0] * steps

        demand_df = pd.DataFrame.from_dict(self.demand_profile)
        # print(demand_df)
        demand_df.to_csv(csv_path, index=False, header=True)

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
                if comp_type in ['HeatPump', 'GasHeatPump', 'HeatPumpFluid',
                                 'HeatPumpQli', 'HeatPumpFluidQli',
                                 'AirHeatPumpFluid', 'UnderfloorHeat']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      temp_profile=
                                                      env.temp_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['GroundHeatPumpFluid']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      temp_profile=
                                                      env.soil_temperature_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['PV', 'SolarThermalCollector',
                                   'SolarThermalCollectorFluid']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      temp_profile=
                                                      env.temp_profile,
                                                      irr_profile=
                                                      env.irr_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['HeatConsumption', 'HeatConsumptionFluid']:
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
                elif comp_type in ['HotWaterConsumption',
                                   'HotWaterConsumptionFluid']:
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

        self.add_energy_flows()

    def update_components(self, cluster):
        """Update the components, which could be influenced by clustering
        methods. The most important items are consumption items and storages:
        consumptions should be replaced by the new clustered profiles and
        storage should take additional assumption."""
        for item in self.topology.index:
            comp_name = self.topology['comp_name'][item]
            if self.topology['comp_type'][item] in ['HeatConsumption',
                                                    'HeatConsumptionFluid']:
                # cluster_profile = pd.Series(cluster.clusterPeriodDict[
                #     'heat_demand']).tolist()
                cluster_profile = cluster['heat_demand'].tolist()
                self.components[comp_name].update_profile(
                    consum_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['ElectricalConsumption']:
                cluster_profile = cluster['elec_demand'].tolist()
                self.components[comp_name].update_profile(
                    consum_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['HotWaterConsumption',
                                                    'HotWaterConsumptionFluid'
                                                    ]:
                # cluster_profile = pd.Series(cluster.clusterPeriodDict[
                #                                 'hot_water_demand']).tolist()
                cluster_profile = cluster['hot_water_demand'].tolist()
                self.components[comp_name].update_profile(
                    consum_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['HeatPump',
                                                    'GasHeatPump', 'PV',
                                                    'SolarThermalCollector',
                                                    'SolarThermalCollectorFluid',
                                                    'UnderfloorHeat',
                                                    ]:
                # cluster_profile = pd.Series(cluster.clusterPeriodDict[
                #                                 'temp']).tolist()
                cluster_profile = cluster['temp'].tolist()
                self.components[comp_name].update_profile(
                    temp_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['PV',
                                                    'SolarThermalCollector',
                                                    'SolarThermalCollectorFluid',
                                                    ]:
                # cluster_profile = pd.Series(cluster.clusterPeriodDict[
                #                                 'irr']).tolist()
                cluster_profile = cluster['irr'].tolist()
                self.components[comp_name].update_profile(
                    irr_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['GroundHeatPumpFluid']:
                cluster_profile = pd.Series(cluster.clusterPeriodDict[
                                                'soil_temp']).tolist()
                self.components[comp_name].update_profile(
                    temp_profile=cluster_profile)
            if isinstance(self.components[comp_name], Storage):
                # The indicator cluster in storage could determine if the
                # cluster function should be called.
                self.components[comp_name].cluster = True

    def add_energy_flows(self):
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
        self.simp_matrix = simp_matrix

        for index, row in simp_matrix.iteritems():
            if len(row[row > 0].index.tolist() +
                   row[row.isnull()].index.tolist()) > 0:
                for input_comp in row[row > 0].index.tolist() + \
                                  row[row.isnull()].index.tolist():
                    if 'heat' in self.components[input_comp].outputs and \
                            'heat' in self.components[index].inputs or \
                            'heat' in self.components[input_comp].inputs and \
                            'heat' in self.components[index].outputs:
                        self.energy_flows['heat'][(input_comp, index)] = None
                        self.components[input_comp].add_energy_flows(
                            'output', 'heat', (input_comp, index))
                        self.components[index].add_energy_flows(
                            'input', 'heat', (input_comp, index))
                    if 'elec' in self.components[input_comp].outputs and \
                            'elec' in self.components[index].inputs or \
                            'elec' in self.components[input_comp].inputs and \
                            'elec' in self.components[index].outputs:
                        self.energy_flows['elec'][(input_comp, index)] = None
                        self.components[input_comp].add_energy_flows(
                            'output', 'elec', (input_comp, index))
                        self.components[index].add_energy_flows(
                            'input', 'elec', (input_comp, index))
                    if 'cool' in self.components[input_comp].outputs and \
                            'cool' in self.components[index].inputs or \
                            'cool' in self.components[input_comp].inputs and \
                            'cool' in self.components[index].outputs:
                        self.energy_flows['cool'][(input_comp, index)] = None
                        self.components[input_comp].add_energy_flows(
                            'output', 'cool', (input_comp, index))
                        self.components[index].add_energy_flows(
                            'input', 'cool', (input_comp, index))
                    if 'gas' in self.components[input_comp].outputs and \
                            'gas' in self.components[index].inputs or \
                            'gas' in self.components[input_comp].inputs and \
                            'gas' in self.components[index].outputs:
                        self.energy_flows['gas'][(input_comp, index)] = None
                        self.components[input_comp].add_energy_flows(
                            'output', 'gas', (input_comp, index))
                        self.components[index].add_energy_flows(
                            'input', 'gas', (input_comp, index))

    def add_subsidy(self, subsidy):
        if subsidy == 'all':
            # todo: need to be updated, after two subsidies are modeled.
            # generate the object at first.
            pass
            # self.subsidy_list.append()
        elif isinstance(subsidy, EEG):
            self.subsidy_list.append(subsidy)
            subsidy.analyze_topo(self)
        else:
            warn("The subsidy " + subsidy + "was not modeled, check again, "
                                            "if something goes wrong.")

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
        # heat_flows = {}
        # for index, row in simp_matrix.iteritems():
        #     # search for Nan value and the mass flow in topology matrix, the
        #     # unit is kg/h.
        #     # print(row[row.isnull()].index.tolist())
        #     if len(row[row > 0].index.tolist() +
        #            row[row.isnull()].index.tolist()) > 0:
        #         for input_comp in row[row > 0].index.tolist() + \
        #                           row[row.isnull()].index.tolist():
        #             energy_flow[(input_comp, index)] = pyo.Var(
        #                 model.time_step, bounds=(0, None))
        #             model.add_component(input_comp + '_' + index,
        #                                 energy_flow[(input_comp, index)])
        #
        #             # Check, if heat is the output of the component,
        #             # input should not be considered. The reason for it is
        #             # avoiding duplicate definition, since in building
        #             # level the input of one component is the output of
        #             # another component.
        #             if 'heat' in self.components[input_comp].outputs and \
        #                     'heat' in self.components[index].inputs or \
        #                     'heat' in self.components[input_comp].inputs and \
        #                     'heat' in self.components[index].outputs:
        #                 heat_flows[(input_comp, index)] = {}
        #                 heat_flows[(index, input_comp)] = {}
        #                 # mass flow from component 'input_comp' to
        #                 # component 'index'.
        #                 heat_flows[(input_comp, index)]['mass'] = \
        #                     pyo.Var(model.time_step, bounds=(0, None))
        #                 model.add_component(input_comp + '_' + index +
        #                                     '_' + 'mass', heat_flows[(
        #                     input_comp, index)]['mass'])
        #                 # mass flow from component 'index' to
        #                 # component 'index'.
        #                 heat_flows[(index, input_comp)]['mass'] = \
        #                     pyo.Var(model.time_step, bounds=(0, None))
        #                 model.add_component(index + '_' + input_comp +
        #                                     '_' + 'mass', heat_flows[(
        #                     index, input_comp)]['mass'])
        #                 # temperature of heat flow from component
        #                 # 'input_comp' to component 'index'.
        #                 heat_flows[(input_comp, index)]['temp'] = \
        #                     pyo.Var(model.time_step, bounds=(0, None))
        #                 model.add_component(input_comp + '_' + index +
        #                                     '_' + 'temp', heat_flows[(
        #                     input_comp, index)]['temp'])
        #                 # temperature of heat flow from component
        #                 # 'index' to component 'input_comp'.
        #                 heat_flows[(index, input_comp)]['temp'] = \
        #                     pyo.Var(model.time_step, bounds=(0, None))
        #                 model.add_component(index + '_' + input_comp +
        #                                     '_' + 'temp', heat_flows[(
        #                     index, input_comp)]['temp'])
        #             # elif 'elec' in self.components[input_comp].outputs and \
        #             #         'elec' in self.components[index].inputs or \
        #             #         'elec' in self.components[input_comp].inputs and \
        #             #         'elec' in self.components[index].outputs:
        #             #     elec_flows.append((index, input_comp))

        # Save the simplified matrix and energy flow for energy balance
        # self.heat_flows = heat_flows

        for energy in self.energy_flows.keys():
            for flow in self.energy_flows[energy]:
                self.energy_flows[energy][flow] = pyo.Var(
                    model.time_step, bounds=(0, 10 ** 8))
                model.add_component(energy + '_' + flow[0] + '_' + flow[1],
                                    self.energy_flows[energy][flow])

                if energy == 'heat':
                    if hasattr(self.components[flow[0]], 'heat_flows_out') and \
                            hasattr(self.components[flow[1]], 'heat_flows_in'):
                        if self.components[flow[0]].heat_flows_out is not None \
                                and self.components[flow[1]].heat_flows_in is \
                                not None:
                            self.heat_flows[flow] = {}
                            self.heat_flows[(flow[1], flow[0])] = {}
                            # mass flow from component 'input_comp' to
                            # component 'index'.
                            self.heat_flows[flow]['mass'] = \
                                pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                            model.add_component(flow[0] + '_' + flow[1] + '_'
                                                + 'mass', self.heat_flows[flow][
                                                    'mass'])
                            # mass flow from component 'index' to
                            # component 'index'.
                            self.heat_flows[(flow[1], flow[0])]['mass'] = \
                                pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                            model.add_component(flow[1] + '_' + flow[0] +
                                                '_' + 'mass', self.heat_flows[(
                                flow[1], flow[0])]['mass'])
                            # temperature of heat flow from component
                            # 'input_comp' to component 'index'.
                            self.heat_flows[flow]['temp'] = \
                                pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                            model.add_component(flow[0] + '_' + flow[1] +
                                                '_' + 'temp', self.heat_flows[
                                                    flow]['temp'])
                            # temperature of heat flow from component
                            # 'index' to component 'input_comp'.
                            self.heat_flows[(flow[1], flow[0])]['temp'] = \
                                pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                            model.add_component(flow[1] + '_' + flow[0] +
                                                '_' + 'temp', self.heat_flows[(
                                flow[1], flow[0])]['temp'])

        total_annual_cost = pyo.Var(bounds=(0, None))
        total_operation_cost = pyo.Var(bounds=(0, None))
        total_annual_revenue = pyo.Var(bounds=(0, None))
        total_other_op_cost = pyo.Var(bounds=(0, None))
        total_pur_subsidy = pyo.Var(bounds=(0, None))
        total_op_subsidy = pyo.Var(bounds=(0, None))
        total_elec_pur = pyo.Var(bounds=(0, None))
        # Attention. The building name should be unique, not same as the comp
        # or project or other buildings.
        model.add_component('annual_cost_' + self.name, total_annual_cost)
        model.add_component('operation_cost_' + self.name, total_operation_cost)
        model.add_component('total_annual_revenue_' + self.name,
                            total_annual_revenue)
        model.add_component('other_op_cost_' + self.name, total_other_op_cost)
        model.add_component('total_pur_subsidy_' + self.name, total_pur_subsidy)
        model.add_component('total_op_subsidy_' + self.name, total_op_subsidy)
        model.add_component('total_elec_pur_' + self.name, total_elec_pur)

        for comp in self.components:
            self.components[comp].add_vars(model)

        if len(self.subsidy_list) >= 1:
            for subsidy in self.subsidy_list:
                subsidy.add_vars(model)

    def add_cons(self, model, env, cluster=None):
        self._constraint_energy_balance(model)
        self._constraint_mass_balance(model)
        # todo (yni): Attention in the optimization for operation cost should
        #  comment constrain for solar area. This should be done automated.
        # self._constraint_solar_area(model)

        self._constraint_total_cost(model)
        self._constraint_operation_cost(model, env, cluster)
        self._constraint_total_revenue(model, env)
        self._constraint_other_op_cost(model)
        self._constraint_elec_pur(model)

        if len(self.subsidy_list) >= 1:
            self._constraint_subsidies(model)
            for subsidy in self.subsidy_list:
                subsidy.add_cons(model)

        for comp in self.components:
            if hasattr(self.components[comp], 'heat_flows_in'):
                if isinstance(self.components[comp].heat_flows_in, list):
                    self.components[comp].add_heat_flows_in(
                        self.heat_flows.keys())
            if hasattr(self.components[comp], 'heat_flows_out'):
                if isinstance(self.components[comp].heat_flows_out, list):
                    self.components[comp].add_heat_flows_out(
                        self.heat_flows.keys())
            self.components[comp].add_cons(model)

        # todo (yni): Attention in the optimization for operation cost should
        #  comment constrain for solar area. This should be done automated.
        for item in self.topology.index:
            comp_type = self.topology['comp_type'][item]
            if comp_type in ['PV', 'SolarThermalCollector',
                             'SolarThermalCollectorFluid']:
                self._constraint_solar_area(model)

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
                        self.components[index].constraint_sum_inputs(
                            model=model, energy_type=energy_type)
                        # input_components = row[row > 0].index.tolist() + \
                        #                    row[row.isnull()].index.tolist()
                        # input_energy = model.find_component('input_' +
                        #                                     energy_type + '_' +
                        #                                     index)
                        # for t in model.time_step:
                        #     model.cons.add(input_energy[t] == sum(
                        #         self.energy_flow[(input_comp, index)][t] for
                        #         input_comp in input_components))

        # Constraints for the outputs
        for index, row in self.simp_matrix.iterrows():
            if self.components[index].outputs is not None:
                for energy_type in self.components[index].outputs:
                    if len(row[row > 0].index.tolist() +
                           row[row.isnull()].index.tolist()) > 0:
                        self.components[index].constraint_sum_outputs(
                            model=model,
                            energy_type=energy_type)
                        # output_components = row[row > 0].index.tolist() + \
                        #                     row[row.isnull()].index.tolist()
                        # output_energy = model.find_component('output_' +
                        #                                      energy_type + '_' +
                        #                                      index)
                        # for t in model.time_step:
                        #     model.cons.add(output_energy[t] == sum(
                        #         self.energy_flow[(index, output_comp)][t] for
                        #         output_comp in output_components))

    def _constraint_solar_area(self, model):
        """The total available solar area should be shared by PV and solar
        thermal collector."""
        # 'solar_area_PV' means the area for PV, 'size_PV' means the peak power.
        #  'size_sollar_coll' means the area of solar collector.
        solar_area_var_list = []
        for component in self.components:
            if isinstance(self.components[component], module_dict['PV']):
                solar_area_var_list.append(model.find_component('solar_area_' +
                                                                component))
            elif isinstance(self.components[component],
                            module_dict['SolarThermalCollectorFluid']):
                solar_area_var_list.append(model.find_component('size_' +
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

    def _constraint_total_cost(self, model):
        """Calculate the total annual cost for the building energy system."""
        bld_annual_cost = model.find_component('annual_cost_' + self.name)
        bld_operation_cost = model.find_component('operation_cost_' + self.name)
        bld_revenue = model.find_component('total_annual_revenue_' + self.name)
        bld_other_op_cost = model.find_component('other_op_cost_' + self.name)

        comp_cost_list = []
        for comp in self.components:
            comp_cost_list.append(model.find_component('annual_cost_' + comp))

        model.cons.add(bld_annual_cost == sum(item for item in
                                              comp_cost_list) +
                       bld_operation_cost + bld_other_op_cost - bld_revenue)

    def _constraint_operation_cost(self, model, env, cluster=None):
        """Calculate the total operation cost for the building energy system."""
        bld_operation_cost = model.find_component('operation_cost_' + self.name)
        bld_other_op_cost = model.find_component('other_op_cost_' + self.name)
        # The following elements (buy_elec, ...) are the energy purchase and
        # sale volume in time series and used to avoid that the constraint
        # added is not executed properly if there is a None. The reason for
        # 8761 steps is the different index of python list and pyomo.
        buy_elec = [0] * (env.time_step + 1)  # unmatched index for python and
        # pyomo
        sell_elec = [0] * (env.time_step + 1)
        buy_gas = [0] * (env.time_step + 1)
        buy_heat = [0] * (env.time_step + 1)

        # comp_cost_list = []
        for comp in self.components:
            # comp_cost_list.append(model.find_component('annual_cost_' + comp))
            if isinstance(self.components[comp],
                          module_dict['ElectricityGrid']):
                if 'elec' in self.components[comp].energy_flows['input'].keys():
                    sell_elec = model.find_component('input_elec_' + comp)
                if 'elec' in self.components[comp].energy_flows[
                    'output'].keys():
                    buy_elec = model.find_component('output_elec_' + comp)
            elif isinstance(self.components[comp], module_dict['GasGrid']):
                buy_gas = model.find_component('output_gas_' + comp)
            elif isinstance(self.components[comp], module_dict['HeatGrid']):
                # todo (yni): take care of the situation for variable mass
                #  flow. the calculation of heat price take the amount of
                #  input energy of heat grid as the denominator. This should
                #  be discussed later. It depends on the business model of
                #  district heating supplier. The reason for taking the output
                #  energy of energy, is that the energy loss of heat grid could
                #  be seen as part of the heat exchanger, so it could reduce the
                #  model complexity.
                buy_heat = model.find_component('output_heat_' + comp)

        if self.bilevel:
            elec_price = model.elec_price
        else:
            elec_price = env.elec_price

        if model.find_component('heat_price'):
            heat_price = model.heat_price
        else:
            heat_price = env.heat_price

        if cluster is None:
            model.cons.add(
                bld_operation_cost == sum(buy_elec[t] * elec_price +
                                          buy_gas[t] * env.gas_price +
                                          buy_heat[t] *
                                          heat_price
                                          for t in model.time_step) +
                bld_other_op_cost)
        else:
            # Attention! The period only for 24 hours is developed,
            # other segments are not considered.
            # period_length = 24
            #
            # nr_day_occur = pd.Series(cluster.clusterPeriodNoOccur).tolist()
            # nr_hour_occur = []
            # for nr_occur in nr_day_occur:
            #     nr_hour_occur += [nr_occur] * 24
            nr_hour_occur = cluster['Occur']

            model.cons.add(
                bld_operation_cost == sum(buy_elec[t] * elec_price *
                                          nr_hour_occur[t - 1] + buy_gas[t] *
                                          env.gas_price * nr_hour_occur[t - 1] +
                                          buy_heat[t] * heat_price *
                                          nr_hour_occur[t - 1]
                                          for t in model.time_step) +
                bld_other_op_cost)

    def _constraint_total_revenue(self, model, env, cluster=None):
        """The total revenue of the building is the sum of the revenue of
        supplied electricity."""
        bld_revenue = model.find_component('total_annual_revenue_' + self.name)

        # The following elements (buy_elec, ...) are the energy purchase and
        # sale volume in time series and used to avoid that the constraint
        # added is not executed properly if there is a None. The reason for
        # 8761 steps is the different index of python list and pyomo.
        sell_elec = [0] * (env.time_step + 1)

        # comp_cost_list = []
        for comp in self.components:
            # comp_cost_list.append(model.find_component('annual_cost_' + comp))
            if isinstance(self.components[comp],
                          module_dict['ElectricityGrid']):
                if 'elec' in self.components[comp].energy_flows['input'].keys():
                    sell_elec = model.find_component('input_elec_' + comp)

        if model.find_component('elec_feed_price'):
            elec_feed_price = model.elec_feed_price
        else:
            elec_feed_price = env.elec_feed_price

        if cluster is None:
            model.cons.add(bld_revenue == sum(sell_elec[t] * elec_feed_price
                                              for t in model.time_step))
        else:
            # Attention! The period only for 24 hours is developed,
            # other segments are not considered.
            # period_length = 24
            #
            # nr_day_occur = pd.Series(cluster.clusterPeriodNoOccur).tolist()
            # nr_hour_occur = []
            # for nr_occur in nr_day_occur:
            #     nr_hour_occur += [nr_occur] * 24
            nr_hour_occur = cluster['Occur']

            model.cons.add(bld_revenue == sum(sell_elec[t] * elec_feed_price *
                                              nr_hour_occur[t - 1] for t in
                                              model.time_step))

    def _constraint_other_op_cost(self, model):
        """Other operation costs includes the costs except the fuel cost. One
        of the most common form ist the start up cost for CHPs."""
        # todo (qli&yni): the other operation cost should be tested with
        #  cluster methods
        bld_other_op_cost = model.find_component('other_op_cost_' + self.name)

        other_op_comp_list = []
        for comp in self.components:
            if self.components[comp].other_op_cost:
                comp_other_op_cost = model.find_component('other_op_cost_' +
                                                          comp)
                other_op_comp_list.append(comp_other_op_cost)

        model.cons.add(bld_other_op_cost == sum(comp_op for comp_op
                                                in other_op_comp_list))

    def _constraint_subsidies(self, model):
        """The subsidies in one building are added up to the total subsidy
        and could be used in the objective of the optimization for minimal
        cost for building holder."""
        # In this model no building subsidies are considered for the building
        # elements like wall or windows. The subsidies for each energy device
        # in building are considered.
        total_pur_subsidy = model.find_component('total_pur_subsidy_' +
                                                 self.name)
        total_op_subsidy = model.find_component('total_op_subsidy_' + self.name)

        pur_subsidy_list = []
        op_subsidy_list = []
        for subsidy in self.subsidy_list:
            subsidy_var = None
            if len(subsidy.components) == 1:
                subsidy_var = model.find_component('subsidy_' + subsidy.name +
                                                   '_' + subsidy.components[0])
            else:
                warn(subsidy.name + " has multiple subsidies for components")

            if subsidy.type == 'purchase':
                pur_subsidy_list.append(subsidy_var)
            elif subsidy.type == 'operate':
                op_subsidy_list.append(subsidy_var)

        if len(pur_subsidy_list) > 0:
            model.cons.add(total_pur_subsidy ==
                           sum(pur_subsidy_list[i] for i in range(len(
                               pur_subsidy_list))))
        else:
            model.cons.add(total_pur_subsidy == 0)

        if len(pur_subsidy_list) > 0:
            model.cons.add(total_op_subsidy ==
                           sum(op_subsidy_list[i] for i in range(len(
                               op_subsidy_list))))
        else:
            model.cons.add(total_op_subsidy == 0)

    def _constraint_elec_pur(self, model):
        """The electricity purchase constraint is added to the model. The
        constraint is added to the model if the electricity is purchased
        from the grid."""
        elec_pur = model.find_component('total_elec_pur_' + self.name)
        for comp in self.components:
            if isinstance(self.components[comp],
                          module_dict['ElectricityGrid']):
                if 'elec' in self.components[comp].energy_flows['output'].keys():
                    buy_elec = model.find_component('output_elec_' + comp)

        model.cons.add(elec_pur == sum(buy_elec[t] for t in model.time_step))
