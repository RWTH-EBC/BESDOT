# Qimin Li
# Datum: 2021/12/12 15:05

import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
import tools.post_processing as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='project_16', typ='building')

# Generate the environment object
#env_16 = Environment(start_time=4329, time_step=3)
env_16 = Environment(start_time=0, time_step=30)
project.add_environment(env_16)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_16 = Building(name='bld_16', area=200, solar_area=50)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
# bld_16.add_thermal_profile('heat', env_16.temp_profile_original, env_16)
bld_16.add_hot_water_profile(env_16)

# todo (qli): solar_coll testen (size_e_boi=0)
#bld_16.demand_profile['hot_water_demand'] = [1.1, 0, 1, 1, 0]
# todo (qli): solar_coll mit e_boi testen
#bld_16.demand_profile['hot_water_demand'] = [6, 0, 6, 1, 0]

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
post_pro.plot_double(result_output_path, "solar_coll", "water_tes", 365, "heat"
                     , "heat")
post_pro.plot_double(result_output_path, "water_tes", "tp_val", 365, "heat",
                     "heat")
post_pro.plot_double(result_output_path, "tp_val", "e_boi", 365, "heat",
                     "heat")
post_pro.plot_double(result_output_path, "e_boi", "hw_cns", 365, "heat",
                     "heat")
'''
post_pro.plot_double_24h(result_output_path, "solar_coll", "water_tes")
post_pro.plot_double_24h(result_output_path, "water_tes", "tp_val")
post_pro.plot_double_24h(result_output_path, "tp_val", "e_boi")
post_pro.plot_double_24h(result_output_path, "e_boi", "hw_cns")