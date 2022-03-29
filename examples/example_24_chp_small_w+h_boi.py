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
project = Project(name='project_24', typ='building')


# Generate the environment object
env_24 = Environment(time_step=3)
project.add_environment(env_24)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_24 = Building(name='bld_24', area=200)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
# bld_24.add_thermal_profile('heat', env_24.temp_profile_original, env_2)

bld_24.demand_profile['heat_demand'] = [9, 10, 0]
bld_24.demand_profile['elec_demand'] = [0, 0, 0]
bld_24.demand_profile['hot_water_demand'] = [1, 0, 0]

# Pre define the building energy system with the topology for different
# components and add components to the building.
# todo: 1 hinter 'chp_fluid_small' kann man löschen oder hinzufügen.
# (keine Auslauftemperaturanforderung)
topo_file = os.path.join(base_path, 'data', 'topology',
                         'chp_fluid_small_w+h_boi.csv')
bld_24.add_topology(topo_file)
bld_24.add_components(project.environment)
project.add_building(bld_24)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='operation_cost')
project.run_optimization('gurobi', save_lp=True, save_result=True)

################################################################################
#                                  Post-processing
################################################################################

result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                  project.name + '_result.csv')
#post_pro.plot_all(result_output_path, time_interval=[0, env_24.time_step])