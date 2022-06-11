"""
This script is used to validate Homostorage class.
"""

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
project = Project(name='project_8_2', typ='building')

# Generate the environment object
env_8 = Environment(time_step=100)
project.add_environment(env_8)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_8 = Building(name='bld_8', area=200)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
# bld_2.add_thermal_profile('heat', env_2.temp_profile_original, env_2)

#bld_8.demand_profile['heat_demand'] = [1, 0, 5, 2] * 50
bld_8.add_thermal_profile('heat', env_8.temp_profile_original, env_8)
# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology',
                         'airheatpump_tp.csv')
bld_8.add_topology(topo_file)
bld_8.add_components(project.environment)
project.add_building(bld_8)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='annual_cost')
project.run_optimization('gurobi', save_lp=True, save_result=True)

################################################################################
result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                  project.name + '_result.csv')
post_pro.plot_all(result_output_path, time_interval=[0, env_8.time_step])
################################################################################

result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                  project.name + '_result.csv')
#post_pro.plot_all(result_output_path, time_interval=[0, env_2.time_step])
