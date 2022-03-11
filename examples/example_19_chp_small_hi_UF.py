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
project = Project(name='project_19', typ='building')


# Generate the environment object
env_19 = Environment(time_step=3)
project.add_environment(env_19)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_19 = Building(name='bld_19', area=200)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
# bld_2.add_thermal_profile('heat', env_2.temp_profile_original, env_2)

bld_19.demand_profile['heat_demand'] = [10, 10, 0]
bld_19.demand_profile["elec_demand"] = [0, 0, 0]

# Pre define the building energy system with the topology for different
# components and add components to the building.
# todo: 1 hinter 'chp_fluid_small' kann man löschen oder hinzufügen.
# (keine Auslauftemperaturanforderung)
topo_file = os.path.join(base_path, 'data', 'topology',
                         'chp_fluid_small_hi_UF.csv')
bld_19.add_topology(topo_file)
bld_19.add_components(project.environment)
project.add_building(bld_19)

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
#post_pro.plot_all(result_output_path, time_interval=[0, env_19.time_step])