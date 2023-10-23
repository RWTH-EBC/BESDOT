import os
from scripts.Project import Project
from scripts.Building import Building
from scripts.Environment import Environment
from scripts.subsidies.country_subsidy_EEG import EEG
from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyComponent
from scripts.subsidies.city_subsidy import CitySubsidyComponent
from scripts.subsidies.state_subsidy import StateSubsidyComponent
from utils.find_bld_typ import find_city_bld_typ
from utils.find_bld_typ import find_state_bld_typ
from utils.find_bld_typ import find_country_bld_typ

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                                  Comment                                     #
################################################################################
eeg_feed_typ = 'Ueberschusseinspeisung'  # Ueberschusseinspeisung, Volleinspeisung
eeg_tariff_rate = 'Feste Verguetung'  # Feste Verguetung, Direkte Vermarktung
# city_bld_typ = 'EFH;ZFH;MFH'  # Allgemein, Bestandbau, Neubau,
# [EFH;ZFH;MFH], [EFH], [EFH;ZFH], [MFH], [NWG], [MFH;NWG]
# state_bld_typ = 'Allgemein'  # Allgemein, Neubau, Bestandbau
user = 'None'
# Baden-Baden: SWBAD; Mannheim: basic, premium; Tuebingen: Stadtwerke Tuebingen;
# Jena: basic, premium
conditions = 'Normal'  # Normal, Exchange premium for oil

####################################################################################

# Generate project and environment object.
project_4 = Project(name='Subsidy_Dusseldorf_KM2', typ='building')
test_env = Environment(time_step=8760, city='Dusseldorf', user=user, conditions=conditions)

city_bld_type_options = find_city_bld_typ(test_env.city)
print("Please select the Building Type for the city of size or "
      "press any key if there are no options:")
for index, option in enumerate(city_bld_type_options, start=1):
    print(f"{index}. {option}")

user_choice = input("Enter the option number: ")

try:
    user_choice = int(user_choice)
    if 1 <= user_choice <= len(city_bld_type_options):
        city_bld_typ_choice = city_bld_type_options[user_choice - 1]
    else:
        print("Invalid option number, using the default value.")
        city_bld_typ_choice = None
except ValueError:
    print("Invalid input, using the default value.")
    city_bld_typ_choice = None

state_bld_type_options = find_state_bld_typ(test_env.state)
print("Please select the Building Type for the state or "
      "press any key if there are no options:")
for index, option in enumerate(state_bld_type_options, start=1):
    print(f"{index}. {option}")

user_choice = input("Enter the option number: ")

try:
    user_choice = int(user_choice)
    if 1 <= user_choice <= len(state_bld_type_options):
        state_bld_typ_choice = state_bld_type_options[user_choice - 1]
    else:
        print("Invalid option number, using the default value.")
        state_bld_typ_choice = None
except ValueError:
    print("Invalid input, using the default value.")
    state_bld_typ_choice = None

country_bld_type_options = find_country_bld_typ(test_env.country)
print("Please select the Building Type for the country or "
      "press any key if there are no options:")
for index, option in enumerate(country_bld_type_options, start=1):
    print(f"{index}. {option}")

user_choice = input("Enter the option number: ")

try:
    user_choice = int(user_choice)
    if 1 <= user_choice <= len(country_bld_type_options):
        country_bld_typ_choice = country_bld_type_options[user_choice - 1]
    else:
        print("Invalid option number, using the default value.")
        country_bld_typ_choice = None
except ValueError:
    print("Invalid input, using the default value.")
    country_bld_typ_choice = None

test_env.city_bld_typ = city_bld_typ_choice
test_env.state_bld_typ = state_bld_typ_choice
test_env.country_bld_typ = country_bld_typ_choice
print(f"Building Types for {test_env.city}: {test_env.city_bld_typ}")
print(f"Building Types for {test_env.state}: {test_env.state_bld_typ}")
print(f"Building Types for {test_env.country}: {test_env.country_bld_typ}")

############################################################################

topo_file = os.path.join(base_path, 'data', 'topology', 'basic_new.csv')

# Generate building object and connect to project.
project_4.add_environment(test_env)
test_bld_4 = Building(name='bld_4', area=300, bld_typ='Verwaltungsgebäude')
test_bld_4.add_thermal_profile('heat', test_env)
test_bld_4.add_elec_profile(test_env.year, test_env)
test_bld_4.add_topology(topo_file)
test_bld_4.add_components(test_env)

print(test_bld_4.components)

component_names = [
                   'HeatPumpAirWater',
                   'HeatPumpBrineWater',
                   'HotWaterStorage', 'PV', 'Battery',
                   'SolarThermalCollectorTube',
                   'SolarThermalCollectorFlatPlate',
                   'GasBoiler', 'ElectricBoiler'
                   ]

# Generate subsidy object EEG for PV and connect to project.
eeg = EEG(feed_type=eeg_feed_typ, tariff_rate=eeg_tariff_rate)
test_bld_4.add_subsidy(eeg)

city_subsidies = []
for name in component_names:
    city_subsidy = CitySubsidyComponent(state=test_env.state,
                                        city=test_env.city,
                                        user=test_env.user,
                                        component_name=name,
                                        bld_typ=test_env.city_bld_typ)

    city_subsidies.append(city_subsidy)

for city_subsidy in city_subsidies:
    test_bld_4.add_subsidy(city_subsidy)

state_subsidies = []
for name in component_names:
    state_subsidy = StateSubsidyComponent(state=test_env.state,
                                          component_name=name,
                                          user=test_env.user,
                                          conditions=test_env.conditions,
                                          bld_typ=test_env.state_bld_typ)

    state_subsidies.append(state_subsidy)

for state_subsidy in state_subsidies:
    test_bld_4.add_subsidy(state_subsidy)

country_subsidies = [CountrySubsidyComponent(country=test_env.country,
                                             component_name=name,
                                             conditions=test_env.conditions,
                                             bld_typ=test_env.country_bld_typ)
                     for name in component_names]

for subsidy in country_subsidies:
    test_bld_4.add_subsidy(subsidy)

project_4.add_building(test_bld_4)

components = [
              'pv', 'water_tes', 'bat',
              'solar_coll_flat_plate',
              'solar_coll_tube',
              'air_water_heat_pump',
              'brine_water_heat_pump',
              'boi', 'e_boi'
              ]

for component in components:
    test_bld_4.components[component].change_cost_model(new_cost_model=2)

for comp in test_bld_4.components.values():
    comp.show_cost_model()

project_4.build_model()
project_4.run_optimization('gurobi', save_lp=True, save_result=True, save_folder='project_4')

for comp_name, comp in test_bld_4.components.items():
    size = project_4.model.find_component('size_' + comp_name).value
    print(f"{comp_name}: size = {size}")
