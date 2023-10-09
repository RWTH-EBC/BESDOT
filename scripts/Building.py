import warnings
import pyomo.environ as pyo
# import numpy as np
# import pandas as pd
from scripts.components.Storage import Storage
from scripts.subsidies.EEG_new import EEG
from scripts.subsidies.city_subsidy_kurz import CitySubsidyComponent
from scripts.subsidies.country_subsidy_BAFA_kurz import CountrySubsidyComponent
from scripts.subsidies.state_subsidy_kurz import StateSubsidyComponent
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

        self.name = name
        self.area = area
        if solar_area is None:
            self.solar_area = self.area * 0.1
        else:
            self.solar_area = solar_area

        # todo: What I want to do is to identify if the building is NWG or not,
        #  for example, if my building is Verwaltungsgebäude, then it is in the
        #  scope of NWG, so that I can directly select NWG in the selection of
        #  the type of building for the subsidy later on.
        nwg_typ = ["Verwaltungsgebäude", "Büro und Dienstleistungsgebäude",
                   "Hochschule und Forschung", "Gesundheitswesen",
                   "Bildungseinrichtungen", "Kultureinrichtungen",
                   "Sporteinrichtungen", "Beherbergen und Verpflegen",
                   "Gewerbliche und industrielle", "Verkaufsstätten",
                   "Technikgebäude"]

        if bld_typ in nwg_typ:
            self.building_typ = 'Verwaltungsgebäude'
        elif bld_typ == 'Wohngebäude':
            self.building_typ = 'Wohngebaude'
        else:
            self.building_typ = bld_typ

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

        self.demand_profile = {"elec_demand": [],
                               "heat_demand": [],
                               "cool_demand": [],
                               "hot_water_demand": [],
                               "gas_demand": []}

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
        demand_df.to_csv(csv_path, index=False, header=True)

    def to_dict(self):
        building_dict = {
            "name": self.name,
            "area": self.area,
            "solar_area": self.solar_area,
            "building_typ": self.building_typ,
            "annual_demand": self.annual_demand,
            "components": [],
            "subsidy_list": self.subsidy_list,
            "bilevel": self.bilevel
        }

        for component in self.components.values():
            component_dict = component.to_dict()
            building_dict["components"].append(component_dict)

        return building_dict

    def add_topology(self, topology):
        topo_matrix = pd.read_csv(topology)
        self.topology = topo_matrix

    def add_components(self, env):
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
                                                      temp_profile=env.temp_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['GroundHeatPumpFluid']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      temp_profile=env.soil_temperature_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['PV', 'SolarThermalCollector',
                                   'SolarThermalCollectorFluid']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      temp_profile=env.temp_profile,
                                                      irr_profile=env.irr_profile,
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['HeatConsumption', 'HeatConsumptionFluid']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      consum_profile=self.demand_profile['heat_demand'],
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type == 'ElectricalConsumption':
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      consum_profile=self.demand_profile['elec_demand'],
                                                      comp_model=comp_model,
                                                      min_size=min_size,
                                                      max_size=max_size,
                                                      current_size=current_size)
                elif comp_type in ['HotWaterConsumption',
                                   'HotWaterConsumptionFluid']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      consum_profile=self.demand_profile['hot_water_demand'],
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
        for item in self.topology.index:
            comp_name = self.topology['comp_name'][item]
            if self.topology['comp_type'][item] in ['HeatConsumption',
                                                    'HeatConsumptionFluid']:
                cluster_profile = cluster['heat_demand'].tolist()
                self.components[comp_name].update_profile(
                    consum_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['ElectricalConsumption']:
                cluster_profile = cluster['elec_demand'].tolist()
                self.components[comp_name].update_profile(
                    consum_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['HotWaterConsumption',
                                                    'HotWaterConsumptionFluid']:
                cluster_profile = cluster['hot_water_demand'].tolist()
                self.components[comp_name].update_profile(
                    consum_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['HeatPump',
                                                    'GasHeatPump', 'PV',
                                                    'SolarThermalCollector',
                                                    'SolarThermalCollectorFluid',
                                                    'UnderfloorHeat', ]:
                cluster_profile = cluster['temp'].tolist()
                self.components[comp_name].update_profile(
                    temp_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['PV', 'SolarThermalCollector',
                                                    'SolarThermalCollectorFluid', ]:
                cluster_profile = cluster['irr'].tolist()
                self.components[comp_name].update_profile(
                    irr_profile=cluster_profile)
            if self.topology['comp_type'][item] in ['GroundHeatPumpFluid']:
                cluster_profile = pd.Series(cluster.clusterPeriodDict[
                                                'soil_temp']).tolist()
                self.components[comp_name].update_profile(
                    temp_profile=cluster_profile)
            if isinstance(self.components[comp_name], Storage):
                self.components[comp_name].cluster = True

    def add_energy_flows(self):
        simp_matrix = self.topology.drop(['comp_type', 'model', 'min_size',
                                          'max_size', 'current_size'], axis=1)
        simp_matrix.set_index(['comp_name'], inplace=True)
        self.simp_matrix = simp_matrix

        for index, row in simp_matrix.iteritems():
            if len(row[row > 0].index.tolist() +
                   row[row.isnull()].index.tolist()) > 0:
                for input_comp in row[row > 0].index.tolist() + \
                                  row[row.isnull()].index.tolist():
                    print(f"Checking component: {input_comp} --> {index}")
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

    def add_eeg_subsidy(self, feed_typ, tariff_rate):
        eeg = EEG(feed_type=feed_typ, tariff_rate=tariff_rate)
        self.subsidy_list.append(eeg)

    def add_city_subsidies(self, state, city, component_names):
        city_subsidies = [
            CitySubsidyComponent(state=state, city=city, component_name=name)
            for name in component_names
        ]
        self.subsidy_list.extend(city_subsidies)

    def add_country_subsidies(self, country, component_names):
        country_subsidies = [
            CountrySubsidyComponent(country=country, component_name=name)
            for name in component_names
        ]
        self.subsidy_list.extend(country_subsidies)

    """
    def add_subsidy(self, subsidy, feed_typ=None, tariff_rate=None,
                    state=None, city=None, country=None):
        if subsidy == 'all':
            all_subsidies = []
            component_names = ['HeatPump', 'PV', 'SolarThermalCollector', 'GasBoiler',
                               'ElectricBoiler', 'Battery', 'HotWaterStorage']

            for subsidy_comp in self.subsidy_list:
                if isinstance(subsidy_comp, EEG):
                    self.add_eeg_subsidy(feed_typ, tariff_rate)
                    all_subsidies.append(subsidy_comp)

                if isinstance(subsidy_comp, CitySubsidyComponent):
                    self.add_city_subsidies(state, city, component_names)
                    all_subsidies.append(subsidy_comp)

                if isinstance(subsidy_comp, CountrySubsidyComponent):
                    self.add_country_subsidies(country, component_names)
                    all_subsidies.append(subsidy_comp)

            for subsidy_comp in all_subsidies:
                subsidy_comp.analyze_topo(self)

            self.subsidy_list.extend(all_subsidies)
        else:
            warn("The subsidy " + subsidy + " was not modeled, check again, "
                 "if something goes wrong.")
    """

    def add_subsidy(self, subsidy, feed_typ=None, tariff_rate=None,
                    state=None, city=None, country=None):
        if subsidy == 'all':
            pass
            """
            all_subsidies = []
            for subsidy_comp in self.subsidy_list:
                component_names = []

                if isinstance(subsidy_comp, EEG):
                    self.add_eeg_subsidy(feed_typ, tariff_rate)

                if isinstance(subsidy_comp, CitySubsidyComponent):
                    self.add_city_subsidies(state, city, component_names)

                if isinstance(subsidy_comp, CountrySubsidyComponent):
                    self.add_country_subsidies(country, component_names)

            for subsidy_comp in all_subsidies:
                subsidy_comp.analyze_topo(self)

            self.subsidy_list.extend(all_subsidies)
            """

        elif isinstance(subsidy, (CitySubsidyComponent, StateSubsidyComponent, CountrySubsidyComponent, EEG)):
            self.subsidy_list.append(subsidy)
            subsidy.analyze_topo(self)
        else:
            warn("The subsidy " + subsidy + "was not modeled, check again, "
                 "if something goes wrong.")

    """
    def add_subsidy(self, subsidy, feed_typ=None, tariff_rate=None,
                    state=None, city=None, country=None):
        if subsidy == 'all':
            all_subsidies = []

            for subsidy_comp in self.subsidy_list:
                if isinstance(subsidy_comp, CitySubsidyComponent) \
                        or isinstance(subsidy_comp, CountrySubsidyComponent)\
                        or isinstance(subsidy_comp, EEG):
                    all_subsidies.append(subsidy_comp)

            for subsidy_comp in all_subsidies:
                subsidy_comp.analyze_topo(self)

            self.subsidy_list.extend(all_subsidies)

        elif isinstance(subsidy, (CitySubsidyComponent, CountrySubsidyComponent, EEG)):
            self.subsidy_list.append(subsidy)
            subsidy.analyze_topo(self)
        else:
            warn("The subsidy " + subsidy + "was not modeled, check again, "
                 "if something goes wrong.")
        """

    def add_vars(self, model):
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
                            self.heat_flows[flow]['mass'] = \
                                pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                            model.add_component(flow[0] + '_' + flow[1] + '_'
                                                + 'mass', self.heat_flows[flow][
                                                    'mass'])
                            self.heat_flows[(flow[1], flow[0])]['mass'] = \
                                pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                            model.add_component(flow[1] + '_' + flow[0] +
                                                '_' + 'mass', self.heat_flows[(flow[1], flow[0])]['mass'])
                            self.heat_flows[flow]['temp'] = \
                                pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                            model.add_component(flow[0] + '_' + flow[1] +
                                                '_' + 'temp', self.heat_flows[
                                                    flow]['temp'])
                            self.heat_flows[(flow[1], flow[0])]['temp'] = \
                                pyo.Var(model.time_step, bounds=(0, 10 ** 8))
                            model.add_component(flow[1] + '_' + flow[0] +
                                                '_' + 'temp', self.heat_flows[(flow[1], flow[0])]['temp'])

        total_annual_cost = pyo.Var(bounds=(0, None))
        total_operation_cost = pyo.Var(bounds=(0, None))
        total_annual_revenue = pyo.Var(bounds=(0, None))
        total_other_op_cost = pyo.Var(bounds=(0, None))
        # total_pur_subsidy = pyo.Var(bounds=(0, None))
        total_op_subsidy = pyo.Var(bounds=(0, None))
        total_elec_pur = pyo.Var(bounds=(0, None))

        model.add_component('annual_cost_' + self.name, total_annual_cost)
        model.add_component('operation_cost_' + self.name, total_operation_cost)
        model.add_component('total_revenue_' + self.name, total_annual_revenue)
        model.add_component('other_op_cost_' + self.name, total_other_op_cost)
        # model.add_component('total_pur_subsidy_' + self.name, total_pur_subsidy)
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
        # self._constraint_solar_area(model)
        self._constraint_total_cost(model)
        self._constraint_operation_cost(model, env, cluster)
        self._constraint_total_revenue(model, env)
        self._constraint_other_op_cost(model)
        self._constraint_elec_pur(model, env)

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
        for index, row in self.simp_matrix.iteritems():
            if self.components[index].inputs is not None:
                for energy_type in self.components[index].inputs:
                    if len(row[row > 0].index.tolist() +
                           row[row.isnull()].index.tolist()) > 0:
                        self.components[index].constraint_sum_inputs(
                            model=model, energy_type=energy_type)

        for index, row in self.simp_matrix.iterrows():
            if self.components[index].outputs is not None:
                for energy_type in self.components[index].outputs:
                    if len(row[row > 0].index.tolist() +
                           row[row.isnull()].index.tolist()) > 0:
                        self.components[index].constraint_sum_outputs(
                            model=model,
                            energy_type=energy_type)

    def _constraint_solar_area(self, model):
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
                            module_dict['SolarThermalCollectorFluid']):
                solar_area_var_list.append(model.find_component('solar_area_' +
                                                                component))
        model.cons.add(sum(item for item in solar_area_var_list) <=
                       self.solar_area)

    def _constraint_mass_balance(self, model):
        if self.heat_flows is not None:
            for heat_flow in self.heat_flows:
                flow_1 = model.find_component(heat_flow[0] + '_' + heat_flow[1]
                                              + '_' + 'mass')
                flow_2 = model.find_component(heat_flow[1] + '_' + heat_flow[0]
                                              + '_' + 'mass')
                for t in model.time_step:
                    if self.simp_matrix[heat_flow[0]][heat_flow[1]] > 0:
                        model.cons.add(flow_1[t] == flow_2[t])
                        model.cons.add(flow_1[t] == self.simp_matrix[
                            heat_flow[0]][heat_flow[1]])
                    elif np.isnan(self.simp_matrix[heat_flow[0]][heat_flow[1]]):
                        model.cons.add(flow_1[t] == flow_2[t])

    def _constraint_total_cost(self, model):
        """Calculate the total annual cost for the building energy system."""
        bld_annual_cost = model.find_component('annual_cost_' + self.name)
        bld_operation_cost = model.find_component('operation_cost_' + self.name)
        bld_other_op_cost = model.find_component('other_op_cost_' + self.name)
        bld_revenue = model.find_component('total_revenue_' + self.name)

        comp_cost_list = []
        for comp in self.components:
            comp_cost_list.append(model.find_component('annual_cost_' + comp))

        model.cons.add(bld_annual_cost == sum(item for item in comp_cost_list) +
                       bld_operation_cost + bld_other_op_cost - bld_revenue)

    def _constraint_operation_cost(self, model, env, cluster=None):
        bld_operation_cost = model.find_component('operation_cost_' + self.name)
        bld_other_op_cost = model.find_component('other_op_cost_' + self.name)
        buy_elec = [0] * (env.time_step + 1)
        buy_gas = [0] * (env.time_step + 1)
        buy_heat = [0] * (env.time_step + 1)

        for comp in self.components:
            if isinstance(self.components[comp],
                          module_dict['ElectricityGrid']):
                if 'elec' in self.components[comp].energy_flows['output'].keys():
                    buy_elec = model.find_component('output_elec_' + comp)
            elif isinstance(self.components[comp], module_dict['GasGrid']):
                buy_gas = model.find_component('output_gas_' + comp)
            elif isinstance(self.components[comp], module_dict['HeatGrid']):
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
        bld_revenue = model.find_component('total_revenue_' + self.name)

        # Check if there are operate subsidies for this building
        op_subsidy_exists = any(subsidy.type == 'operate' for subsidy in self.subsidy_list)

        sell_elec = [0] * (env.time_step + 1)
        sell_elec_pv = [0] * (env.time_step + 1)
        sell_elec_chp = [0] * (env.time_step + 1)

        e_grid_name = None  # todo lji: Explain why this variable is needed.

        for comp in self.components:
            if isinstance(self.components[comp], module_dict['ElectricityGrid']):
                e_grid_name = comp
                if 'elec' in self.components[comp].energy_flows['input'].keys():
                    sell_elec = model.find_component('input_elec_' + e_grid_name)

        for comp in self.components:
            if isinstance(self.components[comp], module_dict['PV']):
                sell_elec_pv = model.find_component('elec_' + comp + '_' + e_grid_name)
                # todo lji: Modify the name of the pv.

        for comp in self.components:
            if isinstance(self.components[comp], module_dict['CHP']):
                sell_elec_chp = model.find_component('elec_' + comp + '_' + e_grid_name)

        if 'CHP' in [comp for comp in self.components]:
            elec_feed_price = env.elec_feed_price_chp
        elif model.find_component('elec_feed_price'):
            elec_feed_price = model.elec_feed_price
        else:
            elec_feed_price = env.elec_feed_price

        if not op_subsidy_exists:
            if cluster is None:
                if any(isinstance(self.components[comp], module_dict['CHP']) for comp in self.components):
                    elec_feed_price_to_use = env.elec_feed_price_chp
                else:
                    elec_feed_price_to_use = elec_feed_price

                model.cons.add(bld_revenue == sum(sell_elec[t] * elec_feed_price_to_use
                                                  for t in model.time_step))
            else:
                nr_hour_occur = cluster['Occur']

                if any(isinstance(self.components[comp], module_dict['CHP']) for comp in self.components):
                    elec_feed_price_to_use = env.elec_feed_price_chp
                else:
                    elec_feed_price_to_use = elec_feed_price

                model.cons.add(bld_revenue == sum(sell_elec[t] * elec_feed_price_to_use *
                                                  nr_hour_occur[t - 1] for t in
                                                  model.time_step))

        else:
            bld_op_subsidy = model.find_component('total_op_subsidy_' + self.name)

            if cluster is None:
                model.cons.add(bld_revenue == sum((sell_elec[t] - sell_elec_pv[t]) * elec_feed_price
                                                  for t in model.time_step) + bld_op_subsidy)
            else:
                nr_hour_occur = cluster['Occur']

                model.cons.add(bld_revenue == sum((sell_elec[t] - sell_elec_pv[t]) * elec_feed_price *
                                                  nr_hour_occur[t - 1] for t in
                                                  model.time_step) + bld_op_subsidy)

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

    def _constraint_subsidies(self, model):
        """The subsidies in one building are added up to the total subsidy
        and could be used in the objective of the optimization for minimal
        cost for building holder."""
        # In this model no building subsidies are considered for the building
        # elements like wall or windows. The subsidies for each energy device
        # in building are considered.
        total_op_subsidy = model.find_component('total_op_subsidy_' + self.name)

        op_subsidy_list = []
        for subsidy in self.subsidy_list:
            subsidy_var = None
            if len(subsidy.components) == 1:
                subsidy_var = model.find_component('subsidy_' + subsidy.name +
                                                   '_' + subsidy.components[0])
            else:
                warn(subsidy.name + " has multiple subsidies for components")

            if subsidy.type == 'operate':
                op_subsidy_list.append(subsidy_var)

        if len(op_subsidy_list) > 0:
            model.cons.add(total_op_subsidy ==
                           sum(op_subsidy_list[i] for i in range(len(
                               op_subsidy_list))))
        else:
            model.cons.add(total_op_subsidy == 0)

    def _constraint_elec_pur(self, model, env):
        buy_elec = [0] * (env.time_step + 1)
        elec_pur = model.find_component('total_elec_pur_' + self.name)
        for comp in self.components:
            if isinstance(self.components[comp],
                          module_dict['ElectricityGrid']):
                if 'elec' in self.components[comp].energy_flows['output'].keys():
                    buy_elec = model.find_component('output_elec_' + comp)

        model.cons.add(elec_pur == sum(buy_elec[t] for t in model.time_step))
