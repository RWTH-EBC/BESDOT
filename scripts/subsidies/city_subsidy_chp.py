import pandas as pd
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy
import warnings

small_nr = 0.00001


class CitySubsidyCHP(Subsidy):
    def __init__(self, state, city):
        super().__init__(enact_year=2023)
        self.name = 'city_subsidy'
        self.components = ['CHP']
        self.type = 'purchase'
        self.energy_pair = []
        self.state = state
        self.city = city
        self.subsidy_data = self.load_subsidy_data()

    def load_subsidy_data(self):
        df = pd.read_csv('city_subsidy_policy_CHP.csv')
        return df

    def analyze_topo(self, building):
        chp_name = None

        for index, item in building.topology.iterrows():
            if item["comp_type"] == "CHP":
                chp_name = item["comp_name"]

        if chp_name is not None:
            self.energy_pair.append([chp_name])
        else:
            warnings.warn("Not found CHP name.")

    def add_cons(self, model):
        chp_name = self.energy_pair[0][0]

        component_size = model.find_component('size_' + chp_name)
        subsidy = model.find_component('subsidy_' + chp_name)

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city:
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
                                   if row['State'] == self.state and row['City'] == self.city]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.energy_pair[0][0]}', dj_subsidy)

    def add_vars(self, model):
        pass
