# Qimin Li
# Datum: 2021/12/12 15:05

import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
import tools.post_solar_chp as post

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = 8760
################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='project_16', typ='building')

# Generate the environment object
# env_16 = Environment(start_time=4329, time_step=3)
env_16 = Environment(start_time=0, time_step=a)
project.add_environment(env_16)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_16 = Building(name='bld_16', area=200, solar_area=50)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
bld_16.add_hot_water_profile(env_16)
# bld_16.add_hot_water_profile_TBL(1968, env_16)

# todo (qli): solar_coll testen (size_e_boi=0)
# bld_16.demand_profile['hot_water_demand'] = [1.1, 0, 1, 1, 0]
# todo (qli): solar_coll mit e_boi testen
# bld_16.demand_profile['hot_water_demand'] = [6, 0, 6, 1, 0]

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology',
                         'solar_coll_TW_THE.csv')
bld_16.add_topology(topo_file)
bld_16.add_components(project.environment)
project.add_building(bld_16)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='annual_cost')
project.run_optimization(save_lp=True, save_result=True)

################################################################################
#                                  Post-processing
################################################################################

result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                  project.name + '_result.csv')
# post_pro.plot_all(result_output_path, time_interval=[0, env_16.time_step])
'''
post_pro.plot_double(result_output_path, "solar_coll", "water_tes", 200, "solar"
                     , "heat")
'''
# post_pro.plot_double_24h(result_output_path, "solar_coll", "water_tes")
# post_pro.plot_double_24h(result_output_path, "water_tes", "tp_val")
# post_pro.plot_double_24h(result_output_path, "tp_val", "e_boi")
# post_pro.plot_double_24h(result_output_path, "e_boi", "hw_cns")
# post_pro.plot_double(result_output_path, "water_tes", "tp_val",150, "heat","heat")

'''
post.step_plot_one_line(result_output_path, env_16.time_step, 
                       'water_tes_tp_val_temp',
                       'Temperatur des Speichers ',
                       r'Temperatur ($^\circ$C)', 1.02)
                       
post.step_plot_two_lines(result_output_path, env_16.time_step, 
                         'inlet_temp_solar_coll',
                         'outlet_temp_solar_coll', 'outlet', 'inlet',
                         'Temperatur der Solarkollektor',
                         r'Temperatur ($^\circ$C)', 1.05)

post.step_plot_two_lines(result_output_path, env_16.time_step, 
                         'input_heat_water_tes',
                         'input_heat_tp_val', 'Input', 'Output',
                         'Energieveränderung des Speichers',
                         r'Leistung (kW)', 1.05)
                         
post.step_plot_one_line(result_output_path, env_16.time_step, 
                       'output_heat_solar_coll',
                       'Wärme aus Solarkollektor', r'Leistung (kW)')
'''
post.print_size(result_output_path)
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
