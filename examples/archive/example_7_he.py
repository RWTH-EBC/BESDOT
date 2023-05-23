"""
This script is used to validate HeatExchanger class.
"""

import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
import utils.post_processing as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='project_7', typ='building')

# Generate the environment object
env_7 = Environment(time_step=24)
project.add_environment(env_7)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_4 = Building(name='bld_7', area=200)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
# bld_4.add_thermal_profile('heat', env_4.temp_profile_original, env_4)
bld_4.demand_profile['heat_demand'] = [2, 0] * 12  # 3.5 infeasible, 3 feasible
bld_4.demand_profile['hot_water_demand'] = [0, 0, 1]

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'heat_exchanger_simp2.csv')
bld_4.add_topology(topo_file)
bld_4.add_components(project.environment)
project.add_building(bld_4)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='operation_cost')
project.run_optimization('gurobi', save_lp=True, save_result=True)

################################################################################
#                                  Post-processing
################################################################################

# result_output_path = os.path.join(base_path, 'data', 'opt_output',
#                                   project.name + '_result.csv')
# post_pro.plot_all(result_output_path, time_interval=[0, env_7.time_step])
