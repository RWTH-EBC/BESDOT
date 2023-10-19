import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
from scripts.subsidies.country_subsidy_EEG import EEG
from scripts.subsidies.city_subsidy_kurz import CitySubsidyComponent
from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyComponent
# import utils.post_solar_chp as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

########################################################################

eeg_feed_typ = 'Ueberschusseinspeisung'  # Ueberschusseinspeisung und Volleinspeisung
eeg_tariff_rate = 'Feste Verguetung'  # Feste Verguetung und Direkte Vermarktung

########################################################################

project_12 = Project(name='project_12_city_subsidy_test_stuttgart_chp', typ='building')
test_env_12 = Environment(time_step=8760, city='Stuttgart', user=None, conditions='Normal')
project_12.add_environment(test_env_12)

test_bld_12 = Building(name='bld_12', area=200)
test_bld_12.add_thermal_profile('heat', test_env_12)
test_bld_12.add_elec_profile(test_env_12.year, test_env_12)

topo_file = os.path.join(base_path, '..', 'data', 'topology', 'chp_fluid_small.csv')
test_bld_12.add_topology(topo_file)
test_bld_12.add_components(test_env_12)

# Generate subsidy object EEG for PV and connect to project.
eeg = EEG(feed_type=eeg_feed_typ, tariff_rate=eeg_tariff_rate)
test_bld_12.add_subsidy(eeg)

component_names = ['PV', 'CHP', 'HotWaterStorage']

city_subsidies = []
for name in component_names:
    subsidy = CitySubsidyComponent(state=test_env_12.state, city=test_env_12.city,
                                   component_name=name)
    city_subsidies.append(subsidy)

for subsidy in city_subsidies:
    test_bld_12.add_subsidy(subsidy)

country_subsidies = [CountrySubsidyComponent(country=test_env_12.country,
                                             component_name=name)
                     for name in component_names]

for subsidy in country_subsidies:
    test_bld_12.add_subsidy(subsidy)

project_12.add_building(test_bld_12)

components = ['pv', 'water_tes', 'chp']
for component in components:
    test_bld_12.components[component].change_cost_model(new_cost_model=0)

for comp in test_bld_12.components.values():
    comp.show_cost_model()

project_12.build_model()
project_12.run_optimization('gurobi', save_lp=True, save_result=True, save_folder='project_12')

for comp_name, comp in test_bld_12.components.items():
    size = project_12.model.find_component('size_' + comp_name).value
    print(f"{comp_name}: size = {size}")
