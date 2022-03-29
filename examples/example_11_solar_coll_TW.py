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
project = Project(name='project_11', typ='building')

# Generate the environment object
#env_11 = Environment(start_time=4329, time_step=3)
env_11 = Environment(start_time=10, time_step=3)
project.add_environment(env_11)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_11 = Building(name='bld_11', area=200, solar_area=50)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
# bld_11.add_thermal_profile('heat', env_11.temp_profile_original, env_11)

# todo: That is another possible demand profile, you could try it for
#  validation
bld_11.demand_profile['hot_water_demand'] = [1.1, 0, 1, 1, 0]

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology',
                         'solar_coll_TW.csv')
bld_11.add_topology(topo_file)
bld_11.add_components(project.environment)
project.add_building(bld_11)

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
#post_pro.plot_all(result_output_path, time_interval=[0, env_11.time_step])