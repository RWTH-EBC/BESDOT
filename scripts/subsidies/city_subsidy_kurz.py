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
    def __init__(self, name, typ, components):
        super().__init__(enact_year=2023)
        self.name = name
        self.components = components
        self.type = typ


class CitySubsidyComponent(CitySubsidy):
    def __init__(self, state, city, user, bld_typ, component_name):
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

        component_size = model.find_component('size_' + comp_name)
        subsidy = model.find_component('subsidy_' + comp_name)

        matching_subsidy_found = False

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and row['User'] == self.user and\
                    row['Building Type'] == self.bld_typ and row['Component'] == self.component_name:
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
                matching_subsidy_found = True

        if not matching_subsidy_found:
            default_subsidy_constraint = pyo.Constraint(expr=subsidy == 0)
            tariff_name = f'{self.name}_{self.energy_pair[0][0]}_default_tariff'
            default_tariff = Disjunct()
            default_tariff.add_component(tariff_name + '_subsidy_constraint', default_subsidy_constraint)
            model.add_component(tariff_name, default_tariff)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{comp_name}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['State'] == self.state and row['City'] == self.city and
                                   row['User'] == self.user and row['Building Type'] == self.bld_typ and
                                   row['Component'] == self.component_name]

        if not matching_subsidy_found:
            tariff_disjunction_expr.append(model.find_component(f'{self.name}_{comp_name}_default_tariff'))

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.user}_'
                            f'{self.bld_typ}_{comp_name}', dj_subsidy)

    def add_vars(self, model):
        pass
