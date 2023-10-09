import os
from scripts.Project import Project
from scripts.Building import Building
from scripts.Environment import Environment
from scripts.subsidies.EEG_new import EEG
from scripts.subsidies.city_subsidy_kurz import CitySubsidyComponent
from scripts.subsidies.state_subsidy_kurz import StateSubsidyComponent
from scripts.subsidies.country_subsidy_BAFA_kurz import CountrySubsidyComponent
# import utils.post_processing as pp

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


##########################################################
#                       Comment                          #
##########################################################
eeg_feed_typ = 'Ueberschusseinspeisung'  # Ueberschusseinspeisung und Volleinspeisung
eeg_tariff_rate = 'Feste Verguetung'  # Feste Verguetung und Direkte Vermarktung
bld_typ = 'None'  # Bestandbau; Neubau; EFH, ZFH, MFH; ZFH; MFH; NWG

#########################################################

# Generate project and environment object.
project_4 = Project(name='project_4_city_subsidy_test_Luebeck_all', typ='building')
test_env = Environment(time_step=8760, city='Luebeck', user=None, conditions='Normal')
topo_file = os.path.join(base_path, 'data', 'topology', 'basic_no_boi.csv')

# Generate building object and connect to project.
project_4.add_environment(test_env)
test_bld_4 = Building(name='bld_4', area=200)
test_bld_4.add_thermal_profile('heat', test_env)
test_bld_4.add_elec_profile(test_env.year, test_env)
test_bld_4.add_topology(topo_file)
test_bld_4.add_components(test_env)

print(test_bld_4.components)

"""
test_bld_4.add_subsidy('all', feed_typ=eeg_feed_typ, tariff_rate=eeg_tariff_rate,
                       state=test_env.state, city=test_env.city, country=test_env.country)
"""

component_names = ['HeatPump', 'HotWaterStorage', 'PV',
                   'Battery', 'SolarThermalCollector']

"""
# Generate subsidy object EEG for PV and connect to project.
eeg = EEG(feed_type=eeg_feed_typ, tariff_rate=eeg_tariff_rate)
test_bld_4.add_subsidy(eeg)

city_subsidies = []
for name in component_names:
    subsidy = CitySubsidyComponent(state=test_env.state, city=test_env.city,
                                   component_name=name)

    city_subsidies.append(subsidy)

for subsidy in city_subsidies:
    test_bld_4.add_subsidy(subsidy)
"""

state_subsidies = []
for name in component_names:
    state_subsidy = StateSubsidyComponent(state=test_env.state,
                                          bld_typ='None',
                                          component_name=name)

    state_subsidies.append(state_subsidy)

for state_subsidy in state_subsidies:
    test_bld_4.add_subsidy(state_subsidy)

"""
country_subsidies = [CountrySubsidyComponent(country=test_env.country, component_name=name)
                     for name in component_names]

for subsidy in country_subsidies:
    test_bld_4.add_subsidy(subsidy)
"""

project_4.add_building(test_bld_4)

components = ['pv', 'water_tes', 'flat_plate_solar_coll', 'tube_solar_coll',
              'bat', 'air_water_heat_pump', 'brine_water_heat_pump']
for component in components:
    test_bld_4.components[component].change_cost_model(new_cost_model=0)

for comp in test_bld_4.components.values():
    comp.show_cost_model()

project_4.build_model()
project_4.run_optimization('gurobi', save_lp=True, save_result=True, save_folder='project_4')

for comp_name, comp in test_bld_4.components.items():
    size = project_4.model.find_component('size_' + comp_name).value
    print(f"{comp_name}: size = {size}")
