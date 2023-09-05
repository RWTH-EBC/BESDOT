import os
import pandas as pd
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy
import warnings

small_nr = 0.00001

script_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_folder, '../..', 'data', 'subsidy', 'city_subsidy_policy.csv')
subsidy_data = pd.read_csv(csv_file_path)


class CitySubsidy(Subsidy):
    def __init__(self, name, typ):
        super().__init__(enact_year=2023)
        self.name = name
        self.components = []
        self.type = typ


class CitySubsidyPV(CitySubsidy):
    def __init__(self, state, city, user, bld_typ):
        super().__init__(name='city_subsidy', typ='purchase')
        self.components = 'PV'
        self.energy_pair = []
        self.state = state
        self.city = city
        self.user = user
        self.bld_typ = bld_typ
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['State'] == self.state) &
                            (subsidy_data['City'] == self.city) &
                            (subsidy_data['Component'] == self.components) &
                            (subsidy_data['User'] == self.user) &
                            (subsidy_data['Building Type'] == self.bld_typ)]

    def analyze_topo(self, building):
        pv_name = None

        for index, item in building.topology.iterrows():
            if item["comp_type"] == "PV":
                pv_name = item["comp_name"]

        if pv_name is not None:
            self.energy_pair.append([pv_name])
        else:
            warnings.warn("Not found PV name.")

    def add_cons(self, model):
        pv_name = self.energy_pair[0][0]

        component_size = model.find_component('size_' + pv_name)
        subsidy = model.find_component('subsidy_' + pv_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and \
               row['User'] == self.user and row['Building Type'] == self.bld_typ \
                    and row['Component'] == 'PV':
                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']
                coefficient = row['Coefficient']
                constant = row['Constant']

                size_constraint = None
                size_constraint_lower = None
                size_constraint_upper = None

                if upper_bound == float('inf'):
                    size_constraint = pyo.Constraint(expr=component_size >= lower_bound)
                else:
                    size_constraint_lower = pyo.Constraint(expr=component_size >= lower_bound)
                    size_constraint_upper = pyo.Constraint(expr=component_size <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == coefficient * component_size + constant)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_size_constraint', size_constraint)
                else:
                    tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)

                tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['State'] == self.state and row['City'] == self.city
                                   and row['User'] == self.user and row['Building Type'] == self.bld_typ
                                   and row['Component'] == self.components]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.user}_'
                            f'{self.bld_typ}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CitySubsidyBattery(CitySubsidy):
    def __init__(self, state, city):
        super().__init__(name='city_subsidy', typ='purchase')
        self.components = 'Battery'
        self.energy_pair = []
        self.state = state
        self.city = city
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['State'] == self.state) &
                            (subsidy_data['City'] == self.city) &
                            (subsidy_data['Component'] == self.components)]

    def analyze_topo(self, building):
        bat_name = None

        for index, item in building.topology.iterrows():
            if item["comp_type"] == "Battery":
                bat_name = item["comp_name"]

        if bat_name is not None:
            self.energy_pair.append([bat_name])
        else:
            warnings.warn("Not found Battery name.")

    def add_cons(self, model):
        bat_name = self.energy_pair[0][0]

        component_size = model.find_component('size_' + bat_name)
        subsidy = model.find_component('subsidy_' + bat_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and row['Component'] == self.components:
                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']
                coefficient = row['Coefficient']
                constant = row['Constant']

                size_constraint = None
                size_constraint_lower = None
                size_constraint_upper = None

                if upper_bound == float('inf'):
                    size_constraint = pyo.Constraint(expr=component_size >= lower_bound)
                else:
                    size_constraint_lower = pyo.Constraint(expr=component_size >= lower_bound)
                    size_constraint_upper = pyo.Constraint(expr=component_size <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == coefficient * component_size + constant)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_size_constraint', size_constraint)
                else:
                    tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)

                tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows() if row['State'] == self.state
                                   and row['City'] == self.city and row['Component'] == self.components]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CitySubsidyGasBoiler(CitySubsidy):
    def __init__(self, state, city):
        super().__init__(name='city_subsidy', typ='purchase')
        self.components = 'GasBoiler'
        self.energy_pair = []
        self.state = state
        self.city = city
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['State'] == self.state) &
                            (subsidy_data['City'] == self.city) &
                            (subsidy_data['Component'] == self.components)]

    def analyze_topo(self, building):
        gas_boiler_name = None

        for index, item in building.topology.iterrows():
            if item["comp_type"] == "GasBoiler":
                gas_boiler_name = item["comp_name"]

        if gas_boiler_name is not None:
            self.energy_pair.append([gas_boiler_name])
        else:
            warnings.warn("Not found GasBoiler name.")

    def add_cons(self, model):
        gas_boiler_name = self.energy_pair[0][0]

        component_size = model.find_component('size_' + gas_boiler_name)
        subsidy = model.find_component('subsidy_' + gas_boiler_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and row['Component'] == self.components:
                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']
                coefficient = row['Coefficient']
                constant = row['Constant']

                size_constraint = None
                size_constraint_lower = None
                size_constraint_upper = None

                if upper_bound == float('inf'):
                    size_constraint = pyo.Constraint(expr=component_size >= lower_bound)
                else:
                    size_constraint_lower = pyo.Constraint(expr=component_size >= lower_bound)
                    size_constraint_upper = pyo.Constraint(expr=component_size <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == coefficient * component_size + constant)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_size_constraint', size_constraint)
                else:
                    tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)

                tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['State'] == self.state and row['City'] == self.city
                                   and row['Component'] == self.components]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CitySubsidyHeatPump(CitySubsidy):
    def __init__(self, state, city):
        super().__init__(name='city_subsidy', typ='purchase')
        self.components = 'HeatPump'
        self.energy_pair = []
        self.state = state
        self.city = city
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['State'] == self.state) &
                            (subsidy_data['City'] == self.city) &
                            (subsidy_data['Component'] == self.components)]

    def analyze_topo(self, building):
        heat_pump_name = None

        for index, item in building.topology.iterrows():
            if item["comp_type"] == "HeatPump":
                heat_pump_name = item["comp_name"]

        if heat_pump_name is not None:
            self.energy_pair.append([heat_pump_name])
        else:
            warnings.warn("Not found HeatPump name.")

    def add_cons(self, model):
        heat_pump_name = self.energy_pair[0][0]

        component_size = model.find_component('size_' + heat_pump_name)
        subsidy = model.find_component('subsidy_' + heat_pump_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and row['Component'] == self.components:
                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']
                coefficient = row['Coefficient']
                constant = row['Constant']

                size_constraint = None
                size_constraint_lower = None
                size_constraint_upper = None

                if upper_bound == float('inf'):
                    size_constraint = pyo.Constraint(expr=component_size >= lower_bound)
                else:
                    size_constraint_lower = pyo.Constraint(expr=component_size >= lower_bound)
                    size_constraint_upper = pyo.Constraint(expr=component_size <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == coefficient * component_size + constant)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_size_constraint', size_constraint)
                else:
                    tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)

                tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['State'] == self.state and row['City'] == self.city
                                   and row['Component'] == self.components]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CitySubsidyElectricBoiler(CitySubsidy):
    def __init__(self, state, city):
        super().__init__(name='city_subsidy', typ='purchase')
        self.components = 'ElectricBoiler'
        self.energy_pair = []
        self.state = state
        self.city = city
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['State'] == self.state) &
                            (subsidy_data['City'] == self.city) &
                            (subsidy_data['Component'] == self.components)]

    def analyze_topo(self, building):
        e_boiler_name = None

        for index, item in building.topology.iterrows():
            if item["comp_type"] == "ElectricBoiler":
                e_boiler_name = item["comp_name"]

        if e_boiler_name is not None:
            self.energy_pair.append([e_boiler_name])
        else:
            warnings.warn("Not found ElectricBoiler name.")

    def add_cons(self, model):
        e_boiler_name = self.energy_pair[0][0]

        component_size = model.find_component('size_' + e_boiler_name)
        subsidy = model.find_component('subsidy_' + e_boiler_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and row['Component'] == self.components:
                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']
                coefficient = row['Coefficient']
                constant = row['Constant']

                size_constraint = None
                size_constraint_lower = None
                size_constraint_upper = None

                if upper_bound == float('inf'):
                    size_constraint = pyo.Constraint(expr=component_size >= lower_bound)
                else:
                    size_constraint_lower = pyo.Constraint(expr=component_size >= lower_bound)
                    size_constraint_upper = pyo.Constraint(expr=component_size <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == coefficient * component_size + constant)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_size_constraint', size_constraint)
                else:
                    tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)

                tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['State'] == self.state and row['City'] == self.city
                                   and row['Component'] == self.components]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CitySubsidySolarThermalCollector(CitySubsidy):
    def __init__(self, state, city):
        super().__init__(name='city_subsidy', typ='purchase')
        self.components = 'SolarThermalCollector'
        self.energy_pair = []
        self.state = state
        self.city = city
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['State'] == self.state) &
                            (subsidy_data['City'] == self.city) &
                            (subsidy_data['Component'] == self.components)]

    def analyze_topo(self, building):
        solar_coll_name = None

        for index, item in building.topology.iterrows():
            if item["comp_type"] == "SolarThermalCollector":
                solar_coll_name = item["comp_name"]

        if solar_coll_name is not None:
            self.energy_pair.append([solar_coll_name])
        else:
            warnings.warn("Not found SolarThermalCollector name.")

    def add_cons(self, model):
        solar_coll_name = self.energy_pair[0][0]

        component_size = model.find_component('size_' + solar_coll_name)
        subsidy = model.find_component('subsidy_' + solar_coll_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and row['Component'] == self.components:
                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']
                coefficient = row['Coefficient']
                constant = row['Constant']

                size_constraint = None
                size_constraint_lower = None
                size_constraint_upper = None

                if upper_bound == float('inf'):
                    size_constraint = pyo.Constraint(expr=component_size >= lower_bound)
                else:
                    size_constraint_lower = pyo.Constraint(expr=component_size >= lower_bound)
                    size_constraint_upper = pyo.Constraint(expr=component_size <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == coefficient * component_size + constant)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_size_constraint', size_constraint)
                else:
                    tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)

                tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['State'] == self.state and row['City'] == self.city
                                   and row['Component'] == self.components]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CitySubsidyHotWaterStorage(CitySubsidy):
    def __init__(self, state, city):
        super().__init__(name='city_subsidy', typ='purchase')
        self.components = 'HotWaterStorage'
        self.energy_pair = []
        self.state = state
        self.city = city
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['State'] == self.state) &
                            (subsidy_data['City'] == self.city) &
                            (subsidy_data['Component'] == self.components)]

    def analyze_topo(self, building):
        water_tes_name = None

        for index, item in building.topology.iterrows():
            if item["comp_type"] == "HotWaterStorage":
                water_tes_name = item["comp_name"]

        if water_tes_name is not None:
            self.energy_pair.append([water_tes_name])
        else:
            warnings.warn("Not found HotWaterStorage name.")

    def add_cons(self, model):
        water_tes_name = self.energy_pair[0][0]

        component_size = model.find_component('size_' + water_tes_name)
        subsidy = model.find_component('subsidy_' + water_tes_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and row['Component'] == self.components:
                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']
                coefficient = row['Coefficient']
                constant = row['Constant']

                size_constraint = None
                size_constraint_lower = None
                size_constraint_upper = None

                if upper_bound == float('inf'):
                    size_constraint = pyo.Constraint(expr=component_size >= lower_bound)
                else:
                    size_constraint_lower = pyo.Constraint(expr=component_size >= lower_bound)
                    size_constraint_upper = pyo.Constraint(expr=component_size <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == coefficient * component_size + constant)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_size_constraint', size_constraint)
                else:
                    tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)

                tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['State'] == self.state and row['City'] == self.city
                                   and row['Component'] == self.components]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass
