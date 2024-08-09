import warnings
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction

from scripts.components.Storage import Storage
from scripts.subsidies.PurchaseSubsidy import PurchaseSubsidy
from scripts.subsidies.OperateSubsidy import OperateSubsidy
from utils.gen_heat_profile import *
from utils.gen_elec_profile import gen_elec_profile
from utils import get_all_class
from utils.gen_hot_water_profile import gen_hot_water_profile
from utils.get_subsidy import check_subsidy


module_dict = get_all_class.run()


class Building(object):
    def __init__(self, name, area, solar_area=None,
                 bld_typ='Single-family house',
                 user='basic',
                 annual_heat_demand=None,
                 annual_elec_demand=None,
                 bilevel=False):
        """
        Initialization for building.
        :param name: name of the building, should be unique
        :param area: area of the building in m^2
        :param solar_area: available area for solar panels in m^2
        :param bld_typ: building type, which is defined in the TEK utils; the
            Building typ could be "Administration building", "Office and service
            buildings", "University and research", "Healthcare", "Educational
            facilities", "Cultural facilities", "Sports facilities",
            "Accommodation and catering", "Commercial and industrial",
            "Retail premises", "Technical buildings", "Single-family house",
            "Multi-family house". Other building types are not considered
        :param user: the user of the building, could be 'basic', 'advanced'.
            it might influence the subsidy of the building
        :param annual_heat_demand: the annual heat demand of the building in kWh
        :param annual_elec_demand: the annual electricity demand of the building
        """
        self.name = name
        self.area = area
        self.type = 'Building'
        if solar_area is None:
            # if the information about the available area for solar of the
            # building is not given, here using a factor of 10% of the total
            # area to assume it.
            self.solar_area = self.area * 0.1
        else:
            self.solar_area = solar_area
        self.building_typ = bld_typ
        self.user = user

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
        # on the air temperature, which is defined in the Environment object.
        # So the method for generate profiles should be called in project
        # rather than in building object.
        self.demand_profile = {"elec_demand": [],
                               "heat_demand": [],
                               "cool_demand": [],
                               "hot_water_demand": [],
                               "gas_demand": []}

        # The topology of the building energy system and all available
        # components in the system, which doesn't mean the components would
        # have to be chosen by optimizer.
        self.topology = None
        self.components = {}
        self.simp_matrix = None
        self.energy_flows = {"elec": {},
                             "heat": {},
                             "cool": {},
                             "gas": {},
                             "biomass": {},
                             "hydrogen": {}}
        self.heat_flows = {}
        self.subsidy_list = []

        self.bilevel_bld = bilevel
        # the heat_supply_business is used to determine the building, if it
        # should be pay the basic price or the power price. The default value is
        # 'demand', which means the building only pay the price for the heat
        # amount it used. If the heat_gird_model is 'power', the building will
        # pay the price for the power it used, which is the maximum power of
        # the building it takes from the heat grid. If the heat_gird_model is
        # 'basic', the building will pay an annual basic price, which is not
        # related to the heat demand.
        self.heat_supply_business = ['demand']
        # self.heat_supply_business = ['demand', 'power', 'basic']

        self.fixed_price_different_by_demand = False
        self.fixed_price_different_by_power = False

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
        Attention!!! The temperature profile could only be provided in project
        object, so this method cannot be called in the initialization of
        building object."""
        # the current version is only for heat, the method could be developed
        # for cool demand.
        if energy_sector == 'heat':
            # heat_demand_profile = gen_heat_profile(self.building_typ,
            #                                        self.area,
            #                                        env.temp_profile_whole,
            #                                        env.year)
            heat_demand_profile = gen_heat_profile(
                self.annual_demand["heat_demand"],
                self.building_typ,
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

    def add_elec_profile(self, env):
        """Generate the electricity profile with the 'Standardlastprofil'
        method. This method could only be called in the Project object,
        because the year is stored in the Environment object"""
        elec_demand_profile = gen_elec_profile(self.annual_demand[
                                                   "elec_demand"],
                                               self.building_typ,
                                               env.year)
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

    def to_dict(self):
        building_dict = {
            "name": self.name,
            "area": self.area,
            "solar_area": self.solar_area,
            "building_typ": self.building_typ,
            "annual_demand": self.annual_demand,
            # "demand_profile": self.demand_profile,
            "components": [],
            "subsidy_list": self.subsidy_list,
            "bilevel": self.bilevel_bld
        }

        for component in self.components.values():
            component_dict = component.to_dict()
            building_dict["components"].append(component_dict)

        return building_dict

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
                if comp_type in ['HeatPump', 'HeatPumpAirWater',
                                 'HeatPumpBrineWater', 'GasHeatPump']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      temp_profile=
                                                      env.temp_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['PV', 'SolarThermalCollector',
                                   'SolarThermalCollectorFlatPlate',
                                   'SolarThermalCollectorTube']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      temp_profile=
                                                      env.temp_profile,
                                                      irr_profile=
                                                      env.irr_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['HeatConsumption']:
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
                elif comp_type in ['HotWaterConsumption']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      consum_profile=
                                                      self.demand_profile[
                                                          'hot_water_demand'],
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
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
        storage should take additional assumption.
        The operation subsidy are also updated, since the operation subsidy is
        related to the energy demand for each time step.
        """
        for item in self.topology.index:
            comp_name = self.topology['comp_name'][item]
            if self.topology['comp_type'][item] in ['HeatConsumption']:
                # cluster_profile = pd.Series(cluster.clusterPeriodDict[
                #     'heat_demand']).tolist()
                cluster_profile = cluster['heat_demand'].tolist()
                self.components[comp_name].update_profile(
                    consum_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['ElectricalConsumption']:
                cluster_profile = cluster['elec_demand'].tolist()
                self.components[comp_name].update_profile(
                    consum_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['HotWaterConsumption'
                                                    ]:
                # cluster_profile = pd.Series(cluster.clusterPeriodDict[
                #                                 'hot_water_demand']).tolist()
                cluster_profile = cluster['hot_water_demand'].tolist()
                self.components[comp_name].update_profile(
                    consum_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['HeatPump',
                                                    'HeatPumpAirWater',
                                                    'HeatPumpBrineWater',
                                                    'GasHeatPump', 'PV',
                                                    'SolarThermalCollector',
                                                    'SolarThermalCollectorFlatPlate',
                                                    'SolarThermalCollectorTube'
                                                    ]:
                # cluster_profile = pd.Series(cluster.clusterPeriodDict[
                #                                 'temp']).tolist()
                cluster_profile = cluster['temp'].tolist()
                self.components[comp_name].update_profile(
                    temp_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['PV',
                                                    'SolarThermalCollector',
                                                    'SolarThermalCollectorFlatPlate',
                                                    'SolarThermalCollectorTube'
                                                    ]:
                # cluster_profile = pd.Series(cluster.clusterPeriodDict[
                #                                 'irr']).tolist()
                cluster_profile = cluster['irr'].tolist()
                self.components[comp_name].update_profile(
                    irr_profile=cluster_profile)
            if isinstance(self.components[comp_name], Storage):
                # The indicator cluster in storage could determine if the
                # cluster function should be called.
                self.components[comp_name].cluster = cluster['Occur'].tolist()

    def update_subsidy(self, cluster):
        """Update the operation subsidy, which is related to the energy demand
        for each time step. The operation subsidy should be updated according
        to the new clustered profiles."""
        for sub in self.subsidy_list:
            if isinstance(sub, OperateSubsidy):
                sub.add_cluster(cluster)

        # Most operation subsidies are related to the device. Like EEG are
        # related to the photovoltaic system and KWKG are related to the CHP.
        for item in self.topology.index:
            comp_name = self.topology['comp_name'][item]
            self.components[comp_name].update_subsidy(cluster)

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

        for index, row in simp_matrix.items():
            if len(row[row > 0].index.tolist() +
                   row[row.isnull()].index.tolist()) > 0:
                for input_comp in row[row > 0].index.tolist() + \
                                  row[row.isnull()].index.tolist():
                    for energy_type in ['heat', 'elec', 'cool', 'gas',
                                        'biomass', 'hydrogen']:
                        self._check_and_add_energy_flow(energy_type,
                                                        input_comp, index)

    def _check_and_add_energy_flow(self, energy_type, input_comp, index):
        if energy_type in self.components[input_comp].outputs and \
                energy_type in self.components[index].inputs or \
                energy_type in self.components[input_comp].inputs and \
                energy_type in self.components[index].outputs:
            self.energy_flows[energy_type][(input_comp, index)] = None
            self.components[input_comp].add_energy_flows(
                'output', energy_type, (input_comp, index))
            self.components[index].add_energy_flows(
                'input', energy_type, (input_comp, index))

    def add_subsidy(self, subsidy_df, building='all'):
        # todo(yni): the current version doesn't consider the building type
        #  and user condition for the subsidy, which should be added later.
        #  It could be modified in the method check_subsidy in find_bld_typ.py
        # find the name of electricity grid, which is strongly related to the
        # operation subsidy.
        elec_grid_name = None
        for elec_grid in self.components.values():
            if elec_grid.component_type == 'ElectricityGrid':
                elec_grid_name = elec_grid.name
                break

        # check if the subsidy is for building or for components
        sub_array = subsidy_df['name'].unique()
        for sub in sub_array:
            sub_type_array = subsidy_df[subsidy_df['name'] == sub][
                'type'].unique()
            sub_level_array = subsidy_df[subsidy_df['name'] == sub][
                'level'].unique()
            sub_apply_array = subsidy_df[subsidy_df['name'] == sub][
                'apply'].unique()
            if 'building' in check_subsidy(sub):
                # This part is not valid for the current version, since the
                # collected subsidies are all for components in Germany.
                if 'purchase' in sub_type_array:
                    self.subsidy_list.append(PurchaseSubsidy(
                        level=sub_level_array[0], name=sub,
                        apply_for='building'))
                elif 'operate' in sub_type_array:
                    self.subsidy_list.append(OperateSubsidy(
                        level=sub_level_array[0], name=sub,
                        apply_for='building'))
            elif 'component' in check_subsidy(sub):
                for comp in self.components.values():
                    if comp.component_type in sub_apply_array:
                        if 'purchase' in sub_type_array:
                            comp.add_subsidy(subsidy_name=sub,
                                             subsidy_type='purchase',
                                             subsidy_level=sub_level_array[0],
                                             user=self.user,
                                             building=building)
                        if 'operate' in sub_type_array:
                            comp.add_subsidy(subsidy_name=sub,
                                             subsidy_type='operate',
                                             subsidy_level=sub_level_array[0],
                                             user=self.user,
                                             building=building,
                                             require_name=elec_grid_name)

    def add_vars(self, model):
        """Add Pyomo variables into the ConcreteModel, which is defined in
        project object. So the model should be given in project object
        build_model.
        The following variable should be assigned:
            Energy flow from a component to another [t]: this should be defined
            according to the component inputs and outputs possibility and the
            building topology. For each time step.
            Total Energy input and output of each component [t]: this should be
            assigned in each component object. For each time step.
            Component size: should be assigned in component object, for once.
        """
        for energy in self.energy_flows.keys():
            for flow in self.energy_flows[energy]:
                self.energy_flows[energy][flow] = pyo.Var(
                    model.time_step, bounds=(0, 10 ** 8))
                model.add_component(energy + '_' + flow[0] + '_' + flow[1],
                                    self.energy_flows[energy][flow])

        # total_annual_cost = pyo.Var(bounds=(0, None)) # this definition
        # might cause infeasible solution, since the following definition
        # would avoid the infeasibility with a positive solution.
        total_annual_cost = pyo.Var()
        total_operation_cost = pyo.Var(bounds=(0, None))
        total_annual_revenue = pyo.Var(bounds=(0, None))
        total_other_op_cost = pyo.Var(bounds=(0, None))
        # total_elec_pur = pyo.Var(bounds=(0, None))
        # Attention. The building name should be unique, not same as the comp
        # or project or other buildings.
        model.add_component('annual_cost_' + self.name, total_annual_cost)
        model.add_component('operation_cost_' + self.name, total_operation_cost)
        model.add_component('total_revenue_' + self.name, total_annual_revenue)
        model.add_component('other_op_cost_' + self.name, total_other_op_cost)
        # model.add_component('total_elec_pur_' + self.name, total_elec_pur)

        for comp in self.components:
            self.components[comp].add_vars(model)

        for sub in self.subsidy_list:
            sub.add_vars(model, self.name)

        if len(self.subsidy_list) >= 1:
            for subsidy in self.subsidy_list:
                subsidy.add_vars(model)

        if self.bilevel_bld:
            building_connection = pyo.Var(within=pyo.Binary, initialize=1) #
            model.add_component('building_connection', building_connection)
            if 'power' in self.heat_supply_business:
                # the maximum power of the building from the heating network
                max_heat_power = pyo.Var(bounds=(0, None))
                model.add_component('max_heat_power', max_heat_power)

            # yso: the fixed price categories will be differentiated based
            # on the use of heat from the heat grid
            if (hasattr(self, 'fixed_price_different_by_demand')
                and self.fixed_price_different_by_demand) \
                    or (hasattr(self, 'fixed_price_different_by_power')
                        and self.fixed_price_different_by_power):
                consider_basic_price = pyo.Var(within=pyo.Binary)
                consider_power_price = pyo.Var(within=pyo.Binary)
                bc_cbp_product = pyo.Var(within=pyo.Binary)  # consider_basic_price和building_connection的乘积
                bc_cpp_product = pyo.Var(within=pyo.Binary) # consider_power_price和building_connection的乘积
                model.add_component('consider_basic_price', consider_basic_price)
                model.add_component('consider_power_price', consider_power_price)
                model.add_component('bc_cbp_product', bc_cbp_product)
                model.add_component('bc_cpp_product', bc_cpp_product)

    def add_cons(self, model, env, cluster=None):
        self._constraint_energy_balance(model)
        self._constraint_total_cost(model)
        self._constraint_operation_cost(model, env, cluster)
        self._constraint_total_revenue(model, env, cluster)
        self._constraint_other_op_cost(model)
        # self._constraint_elec_pur(model, env)

        if self.bilevel_bld:
            # yso: Consider the building’s connection status to the heating network
            self._constraint_building_connection(model, env)
            # yso: to calculate the power price, consider the maximum power from
            # the heating network
            if 'power' in self.heat_supply_business:
                self._constraint_max_heat_power(model, env)
            # yso: the fixed price categories will be differentiated based on the
            # use of heat from the heat grid
            if (hasattr(self, 'fixed_price_different_by_demand')
                and self.fixed_price_different_by_demand) \
                    or (hasattr(self, 'fixed_price_different_by_power')
                        and self.fixed_price_different_by_power):
                self._constraint_fixed_price_different(model, env, cluster)
                self._constraint_bc_cbp_cpp_product(model)

        if len(self.subsidy_list) >= 1:
            for subsidy in self.subsidy_list:
                subsidy.add_cons(model)

        for comp in self.components:
            self.components[comp].add_cons(model)

        constraint_solar_area = False
        for item in self.topology.index:
            comp_type = self.topology['comp_type'][item]
            if comp_type in ['PV', 'SolarThermalCollector',
                             'SolarThermalCollectorFlatPlate',
                             'SolarThermalCollectorTube']:
                constraint_solar_area = True
        if constraint_solar_area:
            self._constraint_solar_area(model)

    def _constraint_energy_balance(self, model):
        """According to the energy system topology, the sum of energy flow
        into a component should be equal to the component inputs. The sum of
        energy flow out of a component to other components should be equal to
        component outputs.
        Attention! If a component has more than 1 inputs or outputs, should
        distinguish between different energy carriers"""
        # todo (yni): the method for more than 1 inputs or outputs should be
        #  tested.

        # Constraints for the inputs
        for index, row in self.simp_matrix.items():
            if self.components[index].inputs is not None:
                for energy_type in self.components[index].inputs:
                    if len(row[row > 0].index.tolist() +
                           row[row.isnull()].index.tolist()) > 0:
                        self.components[index].constraint_sum_inputs(
                            model=model, energy_type=energy_type)

        # Constraints for the outputs
        for index, row in self.simp_matrix.iterrows():
            if self.components[index].outputs is not None:
                for energy_type in self.components[index].outputs:
                    if len(row[row > 0].index.tolist() +
                           row[row.isnull()].index.tolist()) > 0:
                        self.components[index].constraint_sum_outputs(
                            model=model,
                            energy_type=energy_type)

    def _constraint_solar_area(self, model):
        """The total available solar area should be shared by PV and solar
        thermal collector."""
        # 'solar_area_PV' means the area for PV, 'size_PV' means the peak power.
        #  'size_solar_coll' means the area of solar collector.
        solar_area_var_list = []
        for component in self.components:
            if isinstance(self.components[component], module_dict['PV']):
                solar_area_var_list.append(model.find_component('solar_area_' +
                                                                component))
            elif isinstance(self.components[component],
                            module_dict['SolarThermalCollector']):
                solar_area_var_list.append(model.find_component('solar_area_' +
                                                                component))
            elif isinstance(self.components[component],
                            module_dict['SolarThermalCollectorFlatPlate']):
                solar_area_var_list.append(model.find_component('solar_area_' +
                                                                component))
            elif isinstance(self.components[component],
                            module_dict['SolarThermalCollectorTube']):
                solar_area_var_list.append(model.find_component('solar_area_' +
                                                                component))
        model.cons.add(sum(item for item in solar_area_var_list) <=
                       self.solar_area)

    def _constraint_total_cost(self, model):
        """Calculate the total annual cost for the building energy system."""
        bld_annual_cost = model.find_component('annual_cost_' + self.name)
        bld_operation_cost = model.find_component('operation_cost_' + self.name)
        bld_other_op_cost = model.find_component('other_op_cost_' + self.name)
        bld_revenue = model.find_component('total_revenue_' + self.name)

        comp_cost_list = []
        comp_subsidy_list = []
        for comp in self.components:
            comp_cost_list.append(model.find_component('annual_cost_' + comp))
            for sub in self.components[comp].subsidy_list:
                if sub.sub_type == 'purchase':
                    comp_subsidy_list.append(model.find_component(
                        'sub_annuity_' + sub.name + '_' + comp))

        model.cons.add(bld_annual_cost == sum(item for item in comp_cost_list) +
                       bld_operation_cost - bld_revenue -
                       sum(item for item in comp_subsidy_list))

    def _constraint_operation_cost(self, model, env, cluster=None):
        """Calculate the total operation cost for the building energy system."""
        # fixme (yni): the operation cost should consider the revenue and
        #  operate subsidies.
        bld_operation_cost = model.find_component('operation_cost_' + self.name)
        bld_other_op_cost = model.find_component('other_op_cost_' + self.name)

        if self.bilevel_bld:
            if 'power' in self.heat_supply_business:
                max_heat_power = model.find_component('max_heat_power')
            else:
                max_heat_power = 0

            if hasattr(self, 'fixed_price_different_by_demand') \
                    and self.fixed_price_different_by_demand == True:
                bc_cbp_product = model.find_component('bc_cbp_product')
                bc_cpp_product = model.find_component('bc_cpp_product')
            else:
                building_connection = model.find_component('building_connection')
                # building_connection = 0
                # pass
        else:
            building_connection = 0
            max_heat_power = 0

        # The following elements (buy_elec, ...) are the energy purchase and
        # sale volume in time series and used to avoid that the constraint
        # added is not executed properly if there is a None. The reason for
        # 8761 steps is the different index of python list and pyomo.
        buy_elec = [0] * (env.time_step + 1)  # unmatched index for python and
        # pyomo
        # sell_elec = [0] * (env.time_step + 1)
        buy_gas = [0] * (env.time_step + 1)
        buy_heat = [0] * (env.time_step + 1)
        buy_biomass = [0] * (env.time_step + 1)

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
            elif isinstance(self.components[comp], module_dict['BiomassSource']):
                buy_biomass = model.find_component('output_biomass_' + comp)

        if model.find_component('elec_price'):
            elec_price = model.elec_price
        else:
            elec_price = env.elec_price

        if (model.find_component('heat_price') and
                'demand' in self.heat_supply_business):
            if len(model.heat_price.index_set()) == 1:
                heat_price = model.heat_price[0]
            else:
                heat_price = None
                warn('The dynamic heat price is not developed, please check')
        else:
            heat_price = env.heat_price

        if (model.find_component('heat_basic_price') and
                'basic' in self.heat_supply_business):
            if len(model.heat_basic_price.index_set()) == 1:
                heat_basic_price = model.heat_basic_price[0]
            else:
                heat_basic_price = None
                warn('The dynamic heat basic price is not developed, please check')
        else:
            heat_basic_price = 0

        if (model.find_component('heat_power_price') and
                'power' in self.heat_supply_business):
            if len(model.heat_power_price.index_set()) == 1:
                heat_power_price = model.heat_power_price[0]
            else:
                heat_power_price = None
                warn('The dynamic heat power price is not developed, please check')
        else:
            heat_power_price = 0

        gas_price = env.gas_price

        if hasattr(self, 'fixed_price_different_by_demand') \
                and self.fixed_price_different_by_demand == True:
            if cluster is None:
                model.cons.add(
                    bld_operation_cost == sum(buy_elec[t] * elec_price +
                                              buy_gas[t] * gas_price +
                                              buy_heat[t] *
                                              heat_price
                                              for t in model.time_step) +
                    bld_other_op_cost + heat_basic_price * bc_cbp_product +
                    max_heat_power * heat_power_price * bc_cpp_product)
            else:
                nr_hour_occur = cluster['Occur']

                model.cons.add(
                    bld_operation_cost == sum(buy_elec[t] * elec_price *
                                              nr_hour_occur[t - 1] + buy_gas[t] *
                                              gas_price * nr_hour_occur[t - 1] +
                                              buy_heat[t] * heat_price *
                                              nr_hour_occur[t - 1]
                                              for t in model.time_step) +
                    bld_other_op_cost + heat_basic_price * bc_cbp_product +
                    max_heat_power * heat_power_price * bc_cpp_product)
        else:
            if cluster is None:
                model.cons.add(
                    bld_operation_cost == sum(buy_elec[t] * elec_price +
                                            buy_gas[t] * gas_price +
                                            buy_heat[t] * heat_price
                                            for t in model.time_step) +
                    heat_basic_price * building_connection +
                    heat_power_price * max_heat_power +
                    bld_other_op_cost)
            else:
                nr_hour_occur = cluster['Occur']

                model.cons.add(
                    bld_operation_cost == sum(buy_elec[t] * elec_price *
                                            nr_hour_occur[t - 1] + buy_gas[t] *
                                            gas_price * nr_hour_occur[t - 1] +
                                            buy_heat[t] * heat_price *
                                            nr_hour_occur[t - 1]
                                            for t in model.time_step) +
                    heat_basic_price * building_connection +
                    heat_power_price * max_heat_power +
                    bld_other_op_cost)

    def _constraint_total_revenue(self, model, env, cluster=None):
        """The total revenue of the building is the sum of the revenue of
        supplied electricity. The operation subsidies are also considered in
        the revenue."""
        bld_revenue = model.find_component('total_revenue_' + self.name)
        # bld_op_subsidy = model.find_component('total_op_subsidy_' + self.name)
        # bld_op_sub_quantity = model.find_component(
        #     'total_op_sub_quantity_' + self.name)

        # Find out all operation subsidies in the building
        op_subsidy_list = []
        op_subsiy_quantity_list = []
        for comp in self.components:
            for sub in self.components[comp].subsidy_list:
                if sub.sub_type == 'operate':
                    op_subsidy_list.append(model.find_component(
                        'sub_annuity_' + sub.name + '_' + sub.sbj_name))
                    op_subsiy_quantity_list.append(model.find_component(
                        'sub_quantity_' + sub.name + '_' + sub.sbj_name))

        # The following elements (buy_elec, ...) are the energy purchase and
        # sale volume in time series and used to avoid that the constraint
        # added is not executed properly if there is a None. The reason for
        # 8761 steps is the different index of python list and pyomo.
        sell_elec = [0] * (env.time_step + 1)
        # selling heat is not considered in the current version.
        sell_heat = [0] * (env.time_step + 1)

        for comp in self.components:
            if isinstance(self.components[comp],
                          module_dict['ElectricityGrid']):
                if 'elec' in self.components[comp].energy_flows['input'].keys():
                    sell_elec = model.find_component('input_elec_' + comp)
            elif isinstance(self.components[comp], module_dict['HeatGrid']):
                sell_heat = model.find_component('input_heat_' + comp)

        # This part is for the AbstractModel, which is used for the bilevel.
        # For building part, which would just use the given value from the
        # environment. In bilevel model, the value is set as a variable.
        if model.find_component('elec_feed_price'):
            elec_feed_price = model.elec_feed_price
        else:
            elec_feed_price = env.elec_feed_price

        if cluster is None:
            model.cons.add(bld_revenue == sum((sell_elec[t]) * elec_feed_price
                                              for t in model.time_step) +
                           sum(item for item in op_subsidy_list) -
                           sum(item for item in op_subsiy_quantity_list) *
                           elec_feed_price)
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

            model.cons.add(bld_revenue == sum((sell_elec[t]) * elec_feed_price *
                                              nr_hour_occur[t - 1] for t in
                                              model.time_step) +
                           sum(item for item in op_subsidy_list) -
                           sum(item for item in op_subsiy_quantity_list) *
                           elec_feed_price)

    def _constraint_other_op_cost(self, model):
        """Other operation costs includes the costs except the fuel cost. One
        of the most common form ist the start-up cost for CHPs."""
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

    def _constraint_building_connection(self, model, env):
        """This constraint is used to determine the connection status of
        the building and the heating pipe network."""
        building_connection = model.find_component('building_connection')

        M = 1e9

        buy_heat = [0] * (len(model.time_step))
        for comp in self.components:
            if isinstance(self.components[comp], module_dict['HeatGrid']):
                buy_heat = model.find_component('output_heat_' + comp)

        def _building_connection_rule(model,t):
            return buy_heat[t] <= M * building_connection

        model.building_connection_constraint = pyo.Constraint(
                model.time_step, rule=_building_connection_rule)

    def _constraint_max_heat_power(self, model, env):
        """This constraint is used to determine the maximum heat output from heating
        network to building.This value represents the building's peak power, which is
        employed in calculating the heat power price."""
        max_heat_power = model.find_component('max_heat_power')

        buy_heat = [0] * (len(model.time_step))
        for comp in self.components:
            if isinstance(self.components[comp], module_dict['HeatGrid']):
                buy_heat = model.find_component('output_heat_' + comp)

        def _max_heat_power_rule(model, t):
            return max_heat_power >= buy_heat[t]

        model.max_heat_power_constraint = pyo.Constraint(model.time_step,
                                                        rule=_max_heat_power_rule)

    # todo (yni): check it
    def _constraint_fixed_price_different(self, model, env, cluster):
        consider_basic_price = model.find_component('consider_basic_price')
        consider_power_price = model.find_component('consider_power_price')

        if (hasattr(self, 'fixed_price_different_by_demand')
            and self.fixed_price_different_by_demand):
            buy_heat = [0] * len(model.time_step)
            for comp in self.components:
                if isinstance(self.components[comp], module_dict['HeatGrid']):
                    buy_heat = model.find_component('output_heat_' + comp)

            if model.find_component('price_demand_threshold'):
                if len(model.price_demand_threshold.index_set()) == 1:
                    price_demand_threshold = model.price_demand_threshold[0]
                else:
                    price_demand_threshold = None
                    warn('The dynamic price_demand_threshold is not developed, please check')
            else:
                price_demand_threshold = 0

            if cluster is None:
                sum_buy_heat = sum(buy_heat[t] for t in model.time_step)
            else:
                nr_hour_occur = cluster['Occur']
                sum_buy_heat = sum(buy_heat[t] * nr_hour_occur[t - 1] for t in model.time_step)

            epsilon = 1e-12  # 一个非常小的数值，用于近似严格的不等式

            model.PriceDemandDisjunct1 = Disjunct()
            model.PriceDemandDisjunct1.cons = pyo.Constraint(expr=(
                    sum_buy_heat <= price_demand_threshold))
            model.PriceDemandDisjunct1.cons2 = pyo.Constraint(expr=(consider_basic_price == 1))
            model.PriceDemandDisjunct1.cons3 = pyo.Constraint(expr=(consider_power_price == 0))

            model.PriceDemandDisjunct2 = Disjunct()
            model.PriceDemandDisjunct2.cons = pyo.Constraint(expr=(
                    sum_buy_heat >= price_demand_threshold + epsilon))
            model.PriceDemandDisjunct2.cons2 = pyo.Constraint(expr=(consider_basic_price == 0))
            model.PriceDemandDisjunct2.cons3 = pyo.Constraint(expr=(consider_power_price == 1))

            model.price_demand_disjunction = Disjunction(
                expr=[model.PriceDemandDisjunct1, model.PriceDemandDisjunct2])

        elif (hasattr(self, 'fixed_price_different_by_power')
            and self.fixed_price_different_by_power):
            max_heat_power = model.find_component('max_heat_power')

            if model.find_component('price_power_threshold'):
                if len(model.price_power_threshold.index_set()) == 1:
                    price_power_threshold = model.price_power_threshold[0]
                else:
                    price_power_threshold = None
                    warn('The dynamic price_power_threshold is not developed, please check')
            else:
                price_power_threshold = 0

            epsilon = 1e-12  # 一个非常小的数值，用于近似严格的不等式

            model.PricePowerDisjunct1 = Disjunct()
            model.PricePowerDisjunct1.cons = pyo.Constraint(expr=(
                    max_heat_power <= price_power_threshold))
            model.PricePowerDisjunct1.cons2 = pyo.Constraint(expr=(consider_basic_price == 1))
            model.PricePowerDisjunct1.cons3 = pyo.Constraint(expr=(consider_power_price == 0))

            model.PricePowerDisjunct2 = Disjunct()
            model.PricePowerDisjunct2.cons = pyo.Constraint(expr=(
                    max_heat_power >= price_power_threshold + epsilon))
            model.PricePowerDisjunct2.cons2 = pyo.Constraint(expr=(consider_basic_price == 0))
            model.PricePowerDisjunct2.cons3 = pyo.Constraint(expr=(consider_power_price == 1))

            model.price_demand_disjunction = Disjunction(
                expr=[model.PricePowerDisjunct1, model.PricePowerDisjunct2])

        pyo.TransformationFactory('gdp.bigm').apply_to(model, bigM={None: 1e12})

    # todo (yni): check it
    def _constraint_bc_cbp_cpp_product(self, model):
        consider_basic_price = model.find_component('consider_basic_price')
        consider_power_price = model.find_component('consider_power_price')
        building_connection = model.find_component('building_connection')
        bc_cbp_product = model.find_component('bc_cbp_product')
        bc_cpp_product = model.find_component('bc_cpp_product')

        model.cons.add(bc_cpp_product <= building_connection)
        model.cons.add(bc_cpp_product <= consider_power_price)
        model.cons.add(bc_cpp_product >= building_connection + consider_power_price - 1)
        model.cons.add(bc_cbp_product <= building_connection)
        model.cons.add(bc_cbp_product <= consider_basic_price)
        model.cons.add(bc_cbp_product >= building_connection + consider_basic_price - 1)
