import os
import pandas as pd
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy
import warnings

small_nr = 0.00001
large_nr = 10000000

script_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_folder, '../..', 'data', 'subsidy', 'city_subsidy.csv')
subsidy_data = pd.read_csv(csv_file_path)


class CitySubsidy(Subsidy):
    def __init__(self, name, typ, components):
        super().__init__(enact_year=2023)
        self.name = name
        self.components = components
        self.type = typ


class CitySubsidyComponent(CitySubsidy):
    def __init__(self, state, city, component_name, bld_typ='Allgemein', user='None'):
        super().__init__(name='city_subsidy', typ='purchase', components=[component_name])
        self.energy_pair = []
        self.state = state
        self.city = city
        self.user = user
        self.bld_typ = bld_typ
        self.subsidy_data = subsidy_data
        self.component_name = component_name

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['State'] == self.state) &
                            (subsidy_data['City'] == self.city) &
                            (subsidy_data['User'] == self.user) &
                            (subsidy_data['Building Type'] == self.bld_typ) &
                            (subsidy_data['Component'] == self.component_name)]

    def analyze_topo(self, building):
        comp_name = None

        for index, item in building.topology.iterrows():
            if item["comp_type"] == self.component_name:
                comp_name = item["comp_name"]

        if comp_name is not None:
            self.energy_pair.append([comp_name])
        else:
            warnings.warn(f"Not found {self.component_name} name.")

    def add_cons(self, model):
        comp_name = self.energy_pair[0][0]

        invest = model.find_component('invest_' + comp_name)
        area = model.find_component('solar_area_' + comp_name)
        size = model.find_component('size_' + comp_name)
        size_pv = model.find_component('size_pv')
        size_bat = model.find_component('size_bat')
        city_subsidy = model.find_component('city_subsidy_' + comp_name)

        matching_subsidy_found = False

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and row['User'] == self.user and \
                    row['Building Type'] == self.bld_typ and row['Component'] == self.component_name:

                lower_bound_size = row['Size Lower']
                upper_bound_size = row['Size Upper']
                lower_bound_invest = row['Invest Lower']
                upper_bound_invest = row['Invest Upper']
                lower_bound_area = row['Area Lower']
                upper_bound_area = row['Area Upper']
                coefficient_size = row['Size Coefficient']
                constant_size = row['Size Constant']
                coefficient_invest = row['Invest Coefficient']
                constant_invest = row['Invest Constant']
                coefficient_area = row['Area Coefficient']
                constant_area = row['Area Constant']

                size_based_subsidy = False
                invest_based_subsidy = False
                area_based_subsidy = False

                if not pd.isnull(lower_bound_size) and not pd.isnull(upper_bound_size):
                    size_based_subsidy = True

                if not pd.isnull(lower_bound_invest) and not pd.isnull(upper_bound_invest):
                    invest_based_subsidy = True

                if not pd.isnull(lower_bound_area) and not pd.isnull(upper_bound_area):
                    area_based_subsidy = True

                size_constraint_lower = None
                size_constraint_upper = None
                city_subsidy_constraint_size = None

                if size_based_subsidy:
                    if upper_bound_size == float('inf'):
                        upper_bound_size = large_nr

                    size_constraint_lower = pyo.Constraint(expr=size >= lower_bound_size)
                    size_constraint_upper = pyo.Constraint(expr=size <= upper_bound_size)

                    if coefficient_area == 0 and constant_area >= 0:
                        model.cons.add(expr=invest <= constant_size)
                        city_subsidy_constraint_size = pyo.Constraint(expr=city_subsidy == invest)
                    else:
                        city_subsidy_constraint_size = pyo.Constraint(expr=city_subsidy ==
                                                                      coefficient_size * size + constant_size)

                invest_constraint_lower = None
                invest_constraint_upper = None
                city_subsidy_constraint_invest = None

                if invest_based_subsidy:
                    if upper_bound_invest == float('inf'):
                        upper_bound_invest = large_nr

                    invest_constraint_lower = pyo.Constraint(expr=invest >= lower_bound_invest)
                    invest_constraint_upper = pyo.Constraint(expr=invest <= upper_bound_invest)

                    if coefficient_invest == 0 and constant_invest >= 0:
                        model.cons.add(expr=invest <= constant_invest)
                        city_subsidy_constraint_invest = pyo.Constraint(expr=city_subsidy == invest)
                    else:
                        city_subsidy_constraint_invest = pyo.Constraint(expr=city_subsidy ==
                                                                        coefficient_invest * invest + constant_invest)

                area_constraint_lower = None
                area_constraint_upper = None
                city_subsidy_constraint_area = None

                if area_based_subsidy:
                    if upper_bound_area == float('inf'):
                        upper_bound_area = large_nr

                    area_constraint_lower = pyo.Constraint(expr=area >= lower_bound_area)
                    area_constraint_upper = pyo.Constraint(expr=area <= upper_bound_area)

                    if coefficient_area == 0 and constant_area >= 0:
                        model.cons.add(expr=invest <= constant_area)
                        city_subsidy_constraint_area = pyo.Constraint(expr=city_subsidy == invest)
                    else:
                        city_subsidy_constraint_area = pyo.Constraint(expr=city_subsidy ==
                                                                      coefficient_area * area + constant_area)

                tariff_name = f'{self.name}_{comp_name}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if size_based_subsidy:
                    if size_constraint_lower is not None:
                        tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    if size_constraint_lower is not None:
                        tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)
                    if city_subsidy_constraint_size is not None:
                        tariff.add_component(tariff_name + '_city_subsidy_constraint_size',
                                             city_subsidy_constraint_size)

                if invest_based_subsidy:
                    if invest_constraint_lower is not None:
                        tariff.add_component(tariff_name + '_invest_constraint_lower', invest_constraint_lower)
                    if invest_constraint_upper is not None:
                        tariff.add_component(tariff_name + '_invest_constraint_upper', invest_constraint_upper)
                    if city_subsidy_constraint_invest is not None:
                        tariff.add_component(tariff_name + '_city_subsidy_constraint_invest',
                                             city_subsidy_constraint_invest)

                if area_based_subsidy:
                    if area_constraint_lower is not None:
                        tariff.add_component(tariff_name + '_area_constraint_lower', area_constraint_lower)
                    if area_constraint_upper is not None:
                        tariff.add_component(tariff_name + '_area_constraint_upper', area_constraint_upper)
                    if city_subsidy_constraint_area is not None:
                        tariff.add_component(tariff_name + '_city_subsidy_constraint_area',
                                             city_subsidy_constraint_area)

                if self.component_name == 'PV':
                    dis_not_select = Disjunct()
                    not_select_size_pv = pyo.Constraint(expr=size_pv == 0)
                    not_select_size_bat = pyo.Constraint(expr=size_bat == 0)
                    model.add_component('dis_not_select_' + self.component_name, dis_not_select)
                    dis_not_select.add_component('not_select_size_pv_' + self.component_name, not_select_size_pv)
                    dis_not_select.add_component('not_select_size_bat_' + self.component_name, not_select_size_bat)

                    dis_select = Disjunct()
                    select_size_pv = pyo.Constraint(expr=size_pv >= small_nr)
                    select_size_bat = pyo.Constraint(expr=size_bat >= 0)
                    model.add_component('dis_select_' + self.component_name, dis_select)
                    dis_select.add_component('select_size_pv_' + self.component_name, select_size_pv)
                    dis_select.add_component('select_size_bat_' + self.component_name, select_size_bat)

                    dj_size = Disjunction(expr=[dis_not_select, dis_select])
                    model.add_component('disjunction_size_' + self.component_name, dj_size)

                matching_subsidy_found = True

        if not matching_subsidy_found:
            default_subsidy_constraint = pyo.Constraint(expr=city_subsidy == 0)
            tariff_name = f'{self.name}_{comp_name}_default_tariff'
            default_tariff = Disjunct()
            default_tariff.add_component(tariff_name + '_city_subsidy_constraint', default_subsidy_constraint)
            model.add_component(tariff_name, default_tariff)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{comp_name}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['State'] == self.state and row['City'] == self.city and
                                   row['User'] == self.user and (row['Building Type'] == self.bld_typ) and
                                   row['Component'] == self.component_name]

        if not matching_subsidy_found:
            tariff_disjunction_expr.append(model.find_component(f'{self.name}_{comp_name}_default_tariff'))

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.user}_'
                            f'{self.bld_typ}_{comp_name}', dj_subsidy)

    def add_vars(self, model):
        pass
