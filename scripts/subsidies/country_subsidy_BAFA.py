import os
import pandas as pd
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy
import warnings

small_nr = 0.00001

script_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_folder, '../..', 'data', 'subsidy', 'country_subsidy_BAFA.csv')
subsidy_data = pd.read_csv(csv_file_path)


class CountrySubsidyBAFA(Subsidy):
    def __init__(self, name, typ):
        super().__init__(enact_year=2023)
        self.name = name
        self.components = []
        self.type = typ


class CountrySubsidyBAFAHeatPump(CountrySubsidyBAFA):
    def __init__(self, country, conditions):
        super().__init__(name='country_subsidy', typ='purchase')
        self.components = ['HeatPump']
        self.energy_pair = []
        self.country = country
        self.conditions = conditions
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['Country'] == self.country) &
                            (subsidy_data['Conditions'] == self.conditions) &
                            (subsidy_data['Component'] == 'HeatPump')]

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

        # component_size = model.find_component('size_' + heat_pump_name)
        invest = model.find_component('invest_' + heat_pump_name)
        country_subsidy = model.find_component('country_subsidy_' + heat_pump_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['Country'] == self.country and row['Conditions'] == self.conditions \
                    and row['Component'] == 'HeatPump':
                coefficient = row['Coefficient']
                lower_bound = row['Subsidy Lower']
                upper_bound = row['Subsidy Upper']

                subsidy_constraint_lower = None
                subsidy_constraint_upper = None

                if upper_bound == float('inf'):
                    subsidy_constraint_lower = pyo.Constraint(expr=country_subsidy >= lower_bound)
                    subsidy_constraint_upper = pyo.Constraint(expr=country_subsidy <= upper_bound)

                country_subsidy_constraint = pyo.Constraint(expr=country_subsidy == coefficient * invest)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_subsidy_constraint_lower', subsidy_constraint_lower)
                    tariff.add_component(tariff_name + '_subsidy_constraint_upper', subsidy_constraint_upper)

                tariff.add_component(tariff_name + '_country_subsidy_constraint', country_subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['Country'] == self.country and row['Conditions'] == self.conditions
                                   and row['Component'] == 'HeatPump']

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)

        model.add_component(f'disjunction_{self.name}_{self.country}_'
                            f'{self.conditions}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CountrySubsidyBAFASolarThermalCollector(CountrySubsidyBAFA):
    def __init__(self, country, conditions):
        super().__init__(name='country_subsidy', typ='purchase')
        self.components = ['SolarThermalCollector']
        self.energy_pair = []
        self.country = country
        self.conditions = conditions
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['Country'] == self.country) &
                            (subsidy_data['Conditions'] == self.conditions) &
                            (subsidy_data['Component'] == 'SolarThermalCollector')]

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

        # component_size = model.find_component('size_' + heat_pump_name)
        invest = model.find_component('invest_' + solar_coll_name)
        country_subsidy = model.find_component('country_subsidy_' + solar_coll_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['Country'] == self.country and row['Conditions'] == self.conditions\
                    and row['Component'] == 'SolarThermalCollector':
                coefficient = row['Coefficient']
                lower_bound = row['Subsidy Lower']
                upper_bound = row['Subsidy Upper']

                subsidy_constraint = None
                subsidy_constraint_lower = None
                subsidy_constraint_upper = None

                if upper_bound == float('inf'):
                    subsidy_constraint = pyo.Constraint(expr=country_subsidy >= lower_bound)
                else:
                    subsidy_constraint_lower = pyo.Constraint(expr=country_subsidy >= lower_bound)
                    subsidy_constraint_upper = pyo.Constraint(expr=country_subsidy <= upper_bound)

                country_subsidy_constraint = pyo.Constraint(expr=country_subsidy == coefficient * invest)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)
                else:
                    tariff.add_component(tariff_name + '_subsidy_constraint_lower', subsidy_constraint_lower)
                    tariff.add_component(tariff_name + '_subsidy_constraint_upper', subsidy_constraint_upper)

                tariff.add_component(tariff_name + '_country_subsidy_constraint', country_subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['Country'] == self.country and row['Conditions'] == self.conditions
                                   and row['Component'] == 'SolarThermalCollector']

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)

        model.add_component(f'disjunction_{self.name}_{self.country}_'
                            f'{self.conditions}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CountrySubsidyBAFAGasBoiler(CountrySubsidyBAFA):
    def __init__(self, country, conditions):
        super().__init__(name='country_subsidy', typ='purchase')
        self.components = ['GasBoiler']
        self.energy_pair = []
        self.country = country
        self.conditions = conditions
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['Country'] == self.country) &
                            (subsidy_data['Conditions'] == self.conditions) &
                            (subsidy_data['Component'] == 'GasBoiler')]

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

        # component_size = model.find_component('size_' + gas_boiler_name)
        invest = model.find_component('invest_' + gas_boiler_name)
        country_subsidy = model.find_component('country_subsidy_' + gas_boiler_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['Country'] == self.country and row['Conditions'] == self.conditions \
                    and row['Component'] == 'GasBoiler':
                coefficient = row['Coefficient']
                lower_bound = row['Subsidy Lower']
                upper_bound = row['Subsidy Upper']

                subsidy_constraint = None
                subsidy_constraint_lower = None
                subsidy_constraint_upper = None

                if upper_bound == float('inf'):
                    subsidy_constraint = pyo.Constraint(expr=country_subsidy >= lower_bound)
                else:
                    subsidy_constraint_lower = pyo.Constraint(expr=country_subsidy >= lower_bound)
                    subsidy_constraint_upper = pyo.Constraint(expr=country_subsidy <= upper_bound)

                country_subsidy_constraint = pyo.Constraint(expr=country_subsidy == coefficient * invest)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)
                else:
                    tariff.add_component(tariff_name + '_subsidy_constraint_lower', subsidy_constraint_lower)
                    tariff.add_component(tariff_name + '_subsidy_constraint_upper', subsidy_constraint_upper)

                tariff.add_component(tariff_name + '_country_subsidy_constraint', country_subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['Country'] == self.country and row['Conditions'] == self.conditions
                                   and row['Component'] == 'GasBoiler']

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)

        model.add_component(f'disjunction_{self.name}_{self.country}_'
                            f'{self.conditions}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CountrySubsidyBAFAElectricBoiler(CountrySubsidyBAFA):
    def __init__(self, country, conditions):
        super().__init__(name='country_subsidy', typ='purchase')
        self.components = ['ElectricBoiler']
        self.energy_pair = []
        self.country = country
        self.conditions = conditions
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['Country'] == self.country) &
                            (subsidy_data['Conditions'] == self.conditions) &
                            (subsidy_data['Component'] == 'ElectricBoiler')]

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

        # component_size = model.find_component('size_' + e_boiler_name)
        invest = model.find_component('invest_' + e_boiler_name)
        country_subsidy = model.find_component('country_subsidy_' + e_boiler_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['Country'] == self.country and row['Conditions'] == self.conditions \
                    and row['Component'] == 'ElectricBoiler':
                coefficient = row['Coefficient']
                lower_bound = row['Subsidy Lower']
                upper_bound = row['Subsidy Upper']

                subsidy_constraint = None
                subsidy_constraint_lower = None
                subsidy_constraint_upper = None

                if upper_bound == float('inf'):
                    subsidy_constraint = pyo.Constraint(expr=country_subsidy >= lower_bound)
                else:
                    subsidy_constraint_lower = pyo.Constraint(expr=country_subsidy >= lower_bound)
                    subsidy_constraint_upper = pyo.Constraint(expr=country_subsidy <= upper_bound)

                country_subsidy_constraint = pyo.Constraint(expr=country_subsidy == coefficient * invest)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)
                else:
                    tariff.add_component(tariff_name + '_subsidy_constraint_lower', subsidy_constraint_lower)
                    tariff.add_component(tariff_name + '_subsidy_constraint_upper', subsidy_constraint_upper)

                tariff.add_component(tariff_name + '_country_subsidy_constraint', country_subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['Country'] == self.country and row['Conditions'] == self.conditions
                                   and row['Component'] == 'ElectricBoiler']

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)

        model.add_component(f'disjunction_{self.name}_{self.country}_'
                            f'{self.conditions}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CountrySubsidyBAFABattery(CountrySubsidyBAFA):
    def __init__(self, country, conditions):
        super().__init__(name='country_subsidy', typ='purchase')
        self.components = ['Battery']
        self.energy_pair = []
        self.country = country
        self.conditions = conditions
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['Country'] == self.country) &
                            (subsidy_data['Conditions'] == self.conditions) &
                            (subsidy_data['Component'] == 'Battery')]

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

        # component_size = model.find_component('size_' + bat_name)
        invest = model.find_component('invest_' + bat_name)
        country_subsidy = model.find_component('country_subsidy_' + bat_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['Country'] == self.country and row['Conditions'] == self.conditions\
                    and row['Component'] == 'Battery':
                coefficient = row['Coefficient']
                lower_bound = row['Subsidy Lower']
                upper_bound = row['Subsidy Upper']

                subsidy_constraint = None
                subsidy_constraint_lower = None
                subsidy_constraint_upper = None

                if upper_bound == float('inf'):
                    subsidy_constraint = pyo.Constraint(expr=country_subsidy >= lower_bound)
                else:
                    subsidy_constraint_lower = pyo.Constraint(expr=country_subsidy >= lower_bound)
                    subsidy_constraint_upper = pyo.Constraint(expr=country_subsidy <= upper_bound)

                country_subsidy_constraint = pyo.Constraint(expr=country_subsidy == coefficient * invest)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)
                else:
                    tariff.add_component(tariff_name + '_subsidy_constraint_lower', subsidy_constraint_lower)
                    tariff.add_component(tariff_name + '_subsidy_constraint_upper', subsidy_constraint_upper)

                tariff.add_component(tariff_name + '_country_subsidy_constraint', country_subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['Country'] == self.country and row['Conditions'] == self.conditions
                                   and row['Component'] == 'Battery']

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)

        model.add_component(f'disjunction_{self.name}_{self.country}_'
                            f'{self.conditions}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CountrySubsidyBAFAPV(CountrySubsidyBAFA):
    def __init__(self, country, conditions):
        super().__init__(name='country_subsidy', typ='purchase')
        self.components = ['PV']
        self.energy_pair = []
        self.country = country
        self.conditions = conditions
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['Country'] == self.country) &
                            (subsidy_data['Conditions'] == self.conditions) &
                            (subsidy_data['Component'] == 'PV')]

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

        # component_size = model.find_component('size_' + heat_pump_name)
        invest = model.find_component('invest_' + pv_name)
        country_subsidy = model.find_component('country_subsidy_' + pv_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['Country'] == self.country and row['Conditions'] == self.conditions and row['Component'] == 'PV':
                coefficient = row['Coefficient']
                lower_bound = row['Subsidy Lower']
                upper_bound = row['Subsidy Upper']

                subsidy_constraint_lower = None
                subsidy_constraint_upper = None

                if upper_bound == float('inf'):
                    subsidy_constraint_lower = pyo.Constraint(expr=country_subsidy >= lower_bound)
                    subsidy_constraint_upper = pyo.Constraint(expr=country_subsidy <= upper_bound)

                country_subsidy_constraint = pyo.Constraint(expr=country_subsidy == coefficient * invest)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_subsidy_constraint_lower', subsidy_constraint_lower)
                    tariff.add_component(tariff_name + '_subsidy_constraint_upper', subsidy_constraint_upper)

                tariff.add_component(tariff_name + '_country_subsidy_constraint', country_subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['Country'] == self.country and row['Conditions'] == self.conditions
                                   and row['Component'] == 'PV']

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)

        model.add_component(f'disjunction_{self.name}_{self.country}_'
                            f'{self.conditions}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass


class CountrySubsidyBAFAHotWaterStorage(CountrySubsidyBAFA):
    def __init__(self, country, conditions):
        super().__init__(name='country_subsidy', typ='purchase')
        self.components = ['HotWaterStorage']
        self.energy_pair = []
        self.country = country
        self.conditions = conditions
        self.subsidy_data = subsidy_data

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['Country'] == self.country) &
                            (subsidy_data['Conditions'] == self.conditions) &
                            (subsidy_data['Component'] == 'HotWaterStorage')]

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

        # component_size = model.find_component('size_' + heat_pump_name)
        invest = model.find_component('invest_' + water_tes_name)
        country_subsidy = model.find_component('country_subsidy_' + water_tes_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['Country'] == self.country and row['Conditions'] == self.conditions and\
                    row['Component'] == 'HotWaterStorage':
                coefficient = row['Coefficient']
                lower_bound = row['Subsidy Lower']
                upper_bound = row['Subsidy Upper']

                subsidy_constraint_lower = None
                subsidy_constraint_upper = None

                if upper_bound == float('inf'):
                    subsidy_constraint_lower = pyo.Constraint(expr=country_subsidy >= lower_bound)
                    subsidy_constraint_upper = pyo.Constraint(expr=country_subsidy <= upper_bound)

                country_subsidy_constraint = pyo.Constraint(expr=country_subsidy == coefficient * invest)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_subsidy_constraint_lower', subsidy_constraint_lower)
                    tariff.add_component(tariff_name + '_subsidy_constraint_upper', subsidy_constraint_upper)

                tariff.add_component(tariff_name + '_country_subsidy_constraint', country_subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['Country'] == self.country and row['Conditions'] == self.conditions
                                   and row['Component'] == 'HotWaterStorage']

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)

        model.add_component(f'disjunction_{self.name}_{self.country}_'
                            f'{self.conditions}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass
