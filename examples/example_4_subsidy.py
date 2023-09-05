import os
from scripts.Project import Project
from scripts.Building import Building
from scripts.Environment import Environment
from scripts.subsidies.EEG_new import EEG
from scripts.subsidies.city_subsidy import CitySubsidyPV
from scripts.subsidies.city_subsidy import CitySubsidyBattery
from scripts.subsidies.city_subsidy import CitySubsidyGasBoiler
from scripts.subsidies.city_subsidy import CitySubsidyHeatPump
from scripts.subsidies.city_subsidy import CitySubsidyElectricBoiler
from scripts.subsidies.city_subsidy import CitySubsidyHotWaterStorage
from scripts.subsidies.city_subsidy import CitySubsidySolarThermalCollector
from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyBAFAGasBoiler
from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyBAFAElectricBoiler
from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyBAFABattery
from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyBAFASolarThermalCollector
from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyBAFAHeatPump
from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyBAFAPV
from scripts.subsidies.country_subsidy_BAFA import CountrySubsidyBAFAHotWaterStorage
# import utils.post_processing as pp

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_env = Environment(time_step=8760, city='Stuttgart')

# Generate project and environment object.
project_4 = Project(name='project_4_city_subsidy_test_2_stuttgart', typ='building')
project_4.add_environment(test_env)

# Generate building object and connect to project.
test_bld_4 = Building(name='bld_4', area=200)
test_bld_4.add_thermal_profile('heat', test_env)
test_bld_4.add_elec_profile(test_env.year, test_env)

topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_4.add_topology(topo_file)
test_bld_4.add_components(test_env)

# Generate subsidy object EEG for PV and connect to project.
eeg = EEG(feed_type='USE', tariff_rate='Feste Verguetung')
test_bld_4.add_subsidy(eeg)
city_subsidy_pv = CitySubsidyPV(state='BW', city='Stuttgart', bld_typ='default', user='default')
city_subsidy_bat = CitySubsidyBattery(state='BW', city='Stuttgart')
city_subsidy_heat_pump = CitySubsidyHeatPump(state='BW', city='Stuttgart')
city_subsidy_solar_coll = CitySubsidySolarThermalCollector(state='BW', city='Stuttgart')
city_subsidy_gas_boiler = CitySubsidyGasBoiler(state='BW', city='Stuttgart')
city_subsidy_e_boiler = CitySubsidyElectricBoiler(state='BW', city='Stuttgart')
city_subsidy_water_tes = CitySubsidyHotWaterStorage(state='BW', city='Stuttgart')
country_subsidy_pv = CountrySubsidyBAFAPV(country='Germany', conditions='Normal')
country_subsidy_heat_pump = CountrySubsidyBAFAHeatPump(country='Germany', conditions='Normal')
country_subsidy_solar_coll = CountrySubsidyBAFASolarThermalCollector(country='Germany', conditions='Normal')
country_subsidy_gas_boiler = CountrySubsidyBAFAGasBoiler(country='Germany', conditions='Normal')
country_subsidy_e_boiler = CountrySubsidyBAFAElectricBoiler(country='Germany', conditions='Normal')
country_subsidy_bat = CountrySubsidyBAFABattery(country='Germany', conditions='Normal')
country_subsidy_water_tes = CountrySubsidyBAFAHotWaterStorage(country='Germany', conditions='Normal')
test_bld_4.add_subsidy(city_subsidy_pv)
test_bld_4.add_subsidy(city_subsidy_bat)
test_bld_4.add_subsidy(city_subsidy_heat_pump)
test_bld_4.add_subsidy(city_subsidy_solar_coll)
test_bld_4.add_subsidy(city_subsidy_gas_boiler)
test_bld_4.add_subsidy(city_subsidy_e_boiler)
test_bld_4.add_subsidy(city_subsidy_water_tes)
test_bld_4.add_subsidy(country_subsidy_pv)
test_bld_4.add_subsidy(country_subsidy_heat_pump)
test_bld_4.add_subsidy(country_subsidy_solar_coll)
test_bld_4.add_subsidy(country_subsidy_gas_boiler)
test_bld_4.add_subsidy(country_subsidy_e_boiler)
test_bld_4.add_subsidy(country_subsidy_bat)
test_bld_4.add_subsidy(country_subsidy_water_tes)
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

# save model. If only the optimization model is wanted, could use the
# following codes to save the model file. Other model formate like gms,
# mps are also allowed.
# lp_model_path = os.path.join(base_path, 'data', 'opt_output',
#                              test_project.name + '_model.lp')
# test_project.model.write(lp_model_path,
#                          io_options={'symbolic_solver_labels': True})

################################################################################
#                                  Post-processing
################################################################################
# result_file = os.path.join(base_path, 'data', 'opt_output',
#                            'project_1', 'result.csv')
# pp.find_size(result_file)
# pp.plot_all(result_file, [0, 8760])
# pp.plot_all(result_file, [624, 672],
#             save_path=os.path.join(base_path, 'data', 'opt_output', 'project_4'))
