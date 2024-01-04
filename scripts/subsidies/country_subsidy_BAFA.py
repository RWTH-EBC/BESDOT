import os
import pandas as pd
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy
import warnings

small_nr = 0.00001
large_nr = 10000000

script_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_folder, '../..', 'data', 'subsidy', 'country_subsidy_BAFA.csv')
subsidy_data = pd.read_csv(csv_file_path)


class CountrySubsidyBAFA(Subsidy):
    def __init__(self, name, typ, components):
        super().__init__(enact_year=2023)
        self.name = name
        self.components = components
        self.type = typ


class CountrySubsidyComponent(CountrySubsidyBAFA):
    def __init__(self, country, component_name, bld_typ='Allgemein', conditions='Normal'):
        super().__init__(name='country_subsidy', typ='purchase', components=[component_name])
        self.energy_pair = []
        self.country = country
        self.bld_typ = bld_typ
        self.conditions = conditions
        self.subsidy_data = subsidy_data
        self.component_name = component_name

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['Country'] == self.country) &
                            (subsidy_data['Conditions'] == self.conditions) &
                            (subsidy_data['Component'] == self.component_name) &
                            (subsidy_data['Building Type'] == self.bld_typ)]

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
        city_subsidy = model.find_component('city_subsidy_' + comp_name)
        state_subsidy = model.find_component('state_subsidy_' + comp_name)
        country_subsidy = model.find_component('country_subsidy_' + comp_name)

        matching_subsidy_found = False

        for idx, row in self.subsidy_data.iterrows():
            if row['Country'] == self.country \
                    and row['Conditions'] == self.conditions \
                    and row['Component'] == self.component_name \
                    and row['Building Type'] == self.bld_typ:

                lower_bound_invest = row['Invest Lower']
                upper_bound_invest = row['Invest Upper']
                coefficient_invest = row['Invest Coefficient']
                constant_invest = row['Invest Constant']

                if upper_bound_invest == float('inf'):
                    upper_bound_invest = large_nr

                invest_constraint_lower = pyo.Constraint(expr=invest >= lower_bound_invest)
                invest_constraint_upper = pyo.Constraint(expr=invest <= upper_bound_invest)

                if coefficient_invest == 0 and constant_invest >= 0:
                    model.cons.add(expr=invest <= constant_invest)
                    country_subsidy_constraint_invest = pyo.Constraint(expr=country_subsidy == invest)
                else:
                    country_subsidy_constraint_invest = pyo.Constraint(expr=country_subsidy ==
                                                                       coefficient_invest * (invest + city_subsidy
                                                                                             + state_subsidy
                                                                                             + country_subsidy)
                                                                       + constant_invest)

                tariff_name = f'{self.name}_{comp_name}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                tariff.add_component(tariff_name + '_invest_constraint_lower', invest_constraint_lower)
                tariff.add_component(tariff_name + '_invest_constraint_upper', invest_constraint_upper)
                tariff.add_component(tariff_name + '_country_subsidy_constraint_invest',
                                     country_subsidy_constraint_invest)

                matching_subsidy_found = True

        tariff_disjunction_expr = [model.find_component(f'{self.name}_{comp_name}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['Country'] == self.country
                                   and row['Conditions'] == self.conditions
                                   and row['Component'] == self.component_name
                                   and row['Building Type'] == self.bld_typ]

        if not matching_subsidy_found:
            default_subsidy_constraint = pyo.Constraint(expr=country_subsidy == 0)
            tariff_name = f'{self.name}_{self.energy_pair[0][0]}_default_tariff'
            tariff = Disjunct()
            tariff.add_component(tariff_name + '_country_subsidy_constraint', default_subsidy_constraint)
            model.add_component(tariff_name, tariff)

            tariff_disjunction_expr.append(model.find_component(f'{self.name}_{comp_name}_default_tariff'))

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.country}_'
                            f'{self.conditions}_{self.bld_typ}_{comp_name}', dj_subsidy)

    def add_vars(self, model):
        pass
