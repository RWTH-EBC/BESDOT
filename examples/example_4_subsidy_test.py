import os
from scripts.Project import Project
from scripts.Building import Building
from scripts.Environment import Environment
from scripts.subsidies.EEG_new import EEG
from scripts.subsidies.city_subsidy_kurz import CitySubsidyComponent
from scripts.subsidies.country_subsidy_BAFA_kurz import CountrySubsidyComponent
# import utils.post_processing as pp

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_env = Environment(time_step=8760, city='Stuttgart')

# Generate project and environment object.
project_4 = Project(name='project_4_city_subsidy_test_2_stuttgart', typ='building')
project_4.add_environment(test_env)

# Generate building object and connect to project.
test_bld_4 = Building(name='bld_4', area=400)
test_bld_4.add_thermal_profile('heat', test_env)
test_bld_4.add_elec_profile(test_env.year, test_env)

topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_4.add_topology(topo_file)
test_bld_4.add_components(test_env)

# Generate subsidy object EEG for PV and connect to project.
eeg = EEG(feed_type='USE', tariff_rate='Feste Verguetung')
test_bld_4.add_subsidy(eeg)

component_names = ['HeatPump', 'PV', 'SolarThermalCollector',
                   'GasBoiler', 'ElectricBoiler', 'Battery']

city_subsidies = []
for name in component_names:
    if name == 'PV':
        subsidy = CitySubsidyComponent(state='BW', city='Stuttgart', bld_typ='None', user='None',
                                       component_name=name)
    else:
        subsidy = CitySubsidyComponent(state='BW', city='Stuttgart', bld_typ='None', user='None',
                                       component_name=name)
    city_subsidies.append(subsidy)

for subsidy in city_subsidies:
    test_bld_4.add_subsidy(subsidy)

country_subsidies = [CountrySubsidyComponent(country='Germany', conditions='Normal', component_name=name)
                     for name in component_names]
for subsidy in country_subsidies:
    test_bld_4.add_subsidy(subsidy)

project_4.add_building(test_bld_4)

components = ['heat_pump', 'water_tes', 'solar_coll', 'pv', 'bat', 'e_boi', 'boi']
for component in components:
    test_bld_4.components[component].change_cost_model(new_cost_model=0)

for comp in test_bld_4.components.values():
    comp.show_cost_model()

project_4.build_model()
project_4.run_optimization('gurobi', save_lp=True, save_result=True, save_folder='project_4')

for comp_name, comp in test_bld_4.components.items():
    size = project_4.model.find_component('size_' + comp_name).value
    print(f"{comp_name}: size = {size}")
