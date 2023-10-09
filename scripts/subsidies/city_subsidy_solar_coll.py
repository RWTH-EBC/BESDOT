import os
import pandas as pd
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from city_subsidy_kurz import CitySubsidyComponent

small_nr = 0.00001

script_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_folder, '../..', 'data', 'subsidy', 'city_subsidy_solar_coll.csv')
subsidy_data = pd.read_csv(csv_file_path)


class SolarThermalCollectorComponent(CitySubsidyComponent):
    def __init__(self, state, city, bld_typ='None', user='None'):
        super().__init__(state, city, 'SolarThermalCollector', bld_typ, user)

    def add_cons(self, model):
        comp_name = self.energy_pair[0][0]

        component_area = model.find_component('area_' + comp_name)
        subsidy = model.find_component('subsidy_' + comp_name)

        matching_subsidy_found = False

        for idx, row in self.subsidy_data.iterrows():
            if row['State'] == self.state and row['City'] == self.city and row['User'] == self.user and\
                    row['Building Type'] == self.bld_typ and row['Component'] == 'SolarThermalCollector':

                lower_bound = row['Area Lower']
                upper_bound = row['Area Upper']
                coefficient = row['Coefficient']
                constant = row['Constant']

                area_constraint = None
                area_constraint_lower = None
                area_constraint_upper = None

                if upper_bound == float('inf'):
                    area_constraint = pyo.Constraint(expr=component_area >= lower_bound)
                else:
                    area_constraint_lower = pyo.Constraint(expr=component_area >= lower_bound)
                    area_constraint_upper = pyo.Constraint(expr=component_area <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == coefficient * component_area + constant)

                tariff_name = f'{self.name}_{self.energy_pair[0][0]}_tariff_{idx}'
                tariff = Disjunct()
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_area_constraint', area_constraint)
                else:
                    tariff.add_component(tariff_name + '_area_constraint_lower', area_constraint_lower)
                    tariff.add_component(tariff_name + '_area_constraint_upper', area_constraint_upper)

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
                                   row['Component'] == 'SolarThermalCollector']

        if not matching_subsidy_found:
            tariff_disjunction_expr.append(model.find_component(f'{self.name}_{comp_name}_default_tariff'))

        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_{self.name}_{self.state}_{self.city}_{self.user}_'
                            f'{self.bld_typ}_{comp_name}', dj_subsidy)

    def add_vars(self, model):
        pass
