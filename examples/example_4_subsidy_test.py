import os
from scripts.Project import Project
from scripts.Building import Building
from scripts.Environment import Environment
from scripts.subsidies.EEG_new import EEG
from scripts.subsidies.city_subsidy_kurz import CitySubsidyComponent
from scripts.subsidies.country_subsidy_BAFA_kurz import CountrySubsidyComponent
# import utils.post_processing as pp

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


##########################################################
#                       Comment                          #
##########################################################
eeg_feed_typ = 'Ueberschusseinspeisung'  # Ueberschusseinspeisung und Volleinspeisung
eeg_tariff_rate = 'Feste Verguetung'  # Feste Verguetung und Direkte Vermarktung
user = 'None'  # None, basic und premium
bld_typ = 'None'  # None, wg und nwg
wg_typ = "Wohngebaeude"
nwg_typ = ["Verwaltungsgebäude", "Büro und Dienstleistungsgebäude",
           "Hochschule und Forschung", "Gesundheitswesen",
           "Bildungseinrichtungen", "Kultureinrichtungen",
           "Sporteinrichtungen", "Beherbergen und Verpflegen",
           "Gewerbliche und industrielle", "Verkaufsstätten",
           "Technikgebäude"]

#########################################################

# Generate project and environment object.
project_4 = Project(name='project_4_city_subsidy_test_Stuttgart', typ='building')
test_env = Environment(time_step=8760, city='Stuttgart')
project_4.add_environment(test_env)

# Generate building object and connect to project.
test_bld_4 = Building(name='bld_4', area=200)
test_bld_4.add_thermal_profile('heat', test_env)
test_bld_4.add_elec_profile(test_env.year, test_env)

topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_4.add_topology(topo_file)
test_bld_4.add_components(test_env)

print(test_bld_4.components)

# Generate subsidy object EEG for PV and connect to project.
eeg = EEG(feed_type=eeg_feed_typ, tariff_rate=eeg_tariff_rate)
test_bld_4.add_subsidy(eeg)

component_names = ['HeatPump', 'PV', 'SolarThermalCollector', 'GasBoiler',
                   'ElectricBoiler', 'Battery', 'HotWaterStorage']

city_subsidies = []
for name in component_names:
    subsidy = CitySubsidyComponent(state=test_env.state, city=test_env.city,
                                   component_name=name)

    city_subsidies.append(subsidy)

for subsidy in city_subsidies:
    test_bld_4.add_subsidy(subsidy)

country_subsidies = [CountrySubsidyComponent(country=test_env.country, component_name=name)
                     for name in component_names]

for subsidy in country_subsidies:
    test_bld_4.add_subsidy(subsidy)

test_bld_4.add_subsidy('all')

project_4.add_building(test_bld_4)

components = ['heat_pump', 'water_tes', 'solar_coll', 'pv', 'bat', 'boi', 'e_boi']
for component in components:
    test_bld_4.components[component].change_cost_model(new_cost_model=0)

for comp in test_bld_4.components.values():
    comp.show_cost_model()

project_4.build_model()
project_4.run_optimization('gurobi', save_lp=True, save_result=True, save_folder='project_4')

for comp_name, comp in test_bld_4.components.items():
    size = project_4.model.find_component('size_' + comp_name).value
    print(f"{comp_name}: size = {size}")
