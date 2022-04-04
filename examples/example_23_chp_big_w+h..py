import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
import tools.post_processing_solar_chp as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='project_23', typ='building')

# Generate the environment object
env_23 = Environment(time_step=24)
project.add_environment(env_23)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_23 = Building(name='bld_23', area=2000)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
bld_23.add_thermal_profile('heat', env_23.temp_profile_original, env_23)
bld_23.add_elec_profile(2021, env_23)
bld_23.add_hot_water_profile(env_23)
# bld_23.add_hot_water_profile_TBL(1968, env_23)

# bld_23.demand_profile['heat_demand'] = [79, 80, 0]
# bld_23.demand_profile['elec_demand'] = [0, 0, 0]
# bld_23.demand_profile['hot_water_demand'] = [1, 0, 0]

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology',
                         'chp_fluid_big_w+h.csv')
bld_23.add_topology(topo_file)
bld_23.add_components(project.environment)
project.add_building(bld_23)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='annual_cost')
project.run_optimization('gurobi', save_lp=True, save_result=True)

################################################################################
#                                  Post-processing
################################################################################

result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                  project.name + '_result.csv')
# post_pro.plot_all(result_output_path)
