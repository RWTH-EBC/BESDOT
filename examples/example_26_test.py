# Qimin Li
# Datum: 2021/12/12 15:05

import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
import tools.post_solar_chp as post_pro
import tools.plot_cluster as plot_cls

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
days = 12
################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='project_26', typ='building')

# Generate the environment object
# env_27 = Environment(start_time=4329, time_step=3)
env_26 = Environment(start_time=0, time_step=8760)
project.add_environment(env_26)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_26 = Building(name='bld_26', area=2000)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
#bld_27.add_thermal_profile('heat', env_27.temp_profile_original, env_27)
#bld_27.add_elec_profile(2021, env_27)
bld_26.add_thermal_profile('heat', env_26)
bld_26.add_elec_profile(env_26.year, env_26)
bld_26.add_hot_water_profile(env_26)

# Pre define the building energy system with the topology for different
# components and add components to the building.

topo_file = os.path.join(base_path, 'data', 'topology',
                         'test_boi.csv')
'''
topo_file = os.path.join(base_path, 'data', 'topology',
                         'solar_coll_TW_Test.csv')
'''
bld_26.add_topology(topo_file)
bld_26.add_components(project.environment)
project.add_building(bld_26)

################################################################################
#                        Pre-Processing for time clustering
################################################################################
# The profiles could be clustered are: demand profiles, weather profiles and
# prices profiles (if necessary). demand profiles are stored in buildings
# and other information are stored in Environment objects.
#project.time_cluster(nr_periods=days, hours_period=24, save_cls=str(days) + 'day_24hour.csv')
project.time_cluster(nr_periods=days, read_cls=str(days) + 'day_24hour_nwg_qli_1.csv')
plot_cls.step_plot_one_line(von=0, bis=(days + 1) * 24 - 1, nr=str(days), name='day_24hour_nwg_qli.csv', bld='nwg')
plot_cls.step_plot_three_lines(von=0, bis=(days + 1) * 24 - 1, nr=str(days), name='day_24hour_nwg_qli.csv', bld='nwg')

# After clustering need to update the demand profiles and storage assumptions.
for bld in project.building_list:
    bld.update_components(project.cluster)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='annual_cost')
project.run_optimization(solver_name='gurobi', save_lp=True, save_result=True)

################################################################################
#                                  Post-processing
################################################################################

result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                  project.name + '_result.csv')
# post_pro.plot_all(result_output_path, time_interval=[0, env_27.time_step])
post_pro.print_size(result_output_path)
post_pro.step_plot_test_qli(result_output_path, 24*14)
'''
post.step_plot_one_line(result_output_path, env_27.time_step, 
                       'water_tes_tp_val_temp',
                       'Temperatur des Speichers ',
                       r'Temperatur ($^\circ$C)', 1.02)
                       
post.step_plot_two_lines(result_output_path, env_27.time_step, 
                         'inlet_temp_solar_coll',
                         'outlet_temp_solar_coll', 'outlet', 'inlet',
                         'Temperatur der Solarkollektor',
                         r'Temperatur ($^\circ$C)', 1.05)

post.step_plot_two_lines(result_output_path, env_27.time_step, 
                         'input_heat_water_tes',
                         'input_heat_tp_val', 'Input', 'Output',
                         'Energieveränderung des Speichers',
                         r'Leistung (kW)', 1.05)
                        
post.step_plot_one_line(result_output_path, env_27.time_step, 
                       'output_heat_solar_coll',
                       'Wärme aus Solarkollektor', r'Leistung (kW)')
                       
###############################################################################
post.step_plot_one_line(result_output_path, a,
                        'input_elec_e_boi',
                        'Stromverbrauch des Elektroheizkessels ',
                        r'Leistung (kW)', 1.05)

post.step_plot_solar_water_tes(result_output_path, a)
post.step_plot_three_lines(result_output_path, a,
                           'output_heat_water_tes',
                           'input_elec_e_boi', 'input_heat_hw_cns',
                           'Wärme aus Speicher', 'Wärme aus Elektroheizkessel',
                           'Warmwasserbedarf', 'Wärme aus Solarkollector',
                           r'Leistung ('r'kW)', l3='--', n=1.5)

post.step_plot_solar_eff(result_output_path, a,
                         project.environment.temp_profile)
post.step_plot_solar_irr(result_output_path, a,
                         project.environment.irr_profile)
'''