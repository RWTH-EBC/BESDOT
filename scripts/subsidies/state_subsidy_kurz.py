import os
import pandas as pd
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy
import warnings

small_nr = 0.00001

script_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_folder, '../..', 'data', 'subsidy', 'state_subsidy_policy.csv')
subsidy_data = pd.read_csv(csv_file_path)


class StateSubsidy(Subsidy):
    def __init__(self, name, typ, components):
        super().__init__(enact_year=2023)
        self.name = name
        self.components = components
        self.type = typ


class StateSubsidyComponent(StateSubsidy):
    def __init__(self, state, component_name, comp_type='None', bld_typ='None', user='None'):
        super().__init__(name='state_subsidy', typ='purchase', components=[component_name])
        self.energy_pair = []
        self.state = state
        self.comp_type = comp_type
        self.user = user
        self.bld_typ = bld_typ
        self.subsidy_data = subsidy_data
        self.component_name = component_name

    def filter_subsidy_data(self):
        return subsidy_data[(subsidy_data['State'] == self.state) &
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
        state_subsidy = model.find_component('state_subsidy_' + comp_name)

        matching_subsidy_found = False

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['Component Type'] == self.comp_type and row['User'] == self.user and\
                    row['Building Type'] == self.bld_typ and row['Component'] == self.component_name:

                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']
                coefficient = row['Coefficient']
                constant = row['Constant']

                invest_constraint = None
                invest_constraint_lower = None
                invest_constraint_upper = None

                if upper_bound == float('inf'):
                    invest_constraint = pyo.Constraint(expr=invest >= lower_bound)
                else:
                    invest_constraint_lower = pyo.Constraint(expr=invest >= lower_bound)
                    invest_constraint_upper = pyo.Constraint(expr=invest <= upper_bound - small_nr)

                state_subsidy_constraint = pyo.Constraint(expr=state_subsidy == coefficient * invest + constant)

                tariff_name = f'{self.name}_{comp_name}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_invest_constraint', invest_constraint)
                else:
                    tariff.add_component(tariff_name + '_invest_constraint_lower', invest_constraint_lower)
                    tariff.add_component(tariff_name + '_invest_constraint_upper', invest_constraint_upper)

                tariff.add_component(tariff_name + '_state_subsidy_constraint', state_subsidy_constraint)

                matching_subsidy_found = True

        # Check if matching subsidy was found, if not, create default tariff
        if not matching_subsidy_found:
            default_subsidy_constraint = pyo.Constraint(expr=state_subsidy == 0)
            tariff_name = f'{self.name}_{comp_name}_default_tariff'
            tariff = Disjunct()
            tariff.add_component(tariff_name + '_state_subsidy_constraint', default_subsidy_constraint)
            model.add_component(tariff_name, tariff)

        # Create a list of tariffs for the Disjunction
        tariff_disjunction_expr = [model.find_component(f'{self.name}_{comp_name}_tariff_{idx}')
                                   for idx, row in self.subsidy_data.iterrows()
                                   if row['State'] == self.state and row['User'] == self.user
                                   and row['Component Type'] == self.comp_type and row['Building Type'] == self.bld_typ
                                   and row['Component'] == self.component_name]

        # Add the default tariff to the list if no matching subsidy was found
        if not matching_subsidy_found:
            tariff_disjunction_expr.append(model.find_component(f'{self.name}_{comp_name}_default_tariff'))

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.comp_type}_{self.user}_'
                            f'{self.bld_typ}_{comp_name}', dj_subsidy)

    def add_vars(self, model):
        pass
