"""
This script is used to validate standardboiler class.
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
project = Project(name='project_24_cls', typ='building')

# Generate the environment object
env_24 = Environment(time_step=8760)
project.add_environment(env_24)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_24 = Building(name='bld_24', area=200)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
bld_24.add_thermal_profile('heat', env_24)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology',
                         'threeportvalve.csv')
bld_24.add_topology(topo_file)
bld_24.add_components(project.environment)
project.add_building(bld_24)

################################################################################
#                        Pre-Processing for time clustering
################################################################################
# The profiles could be clustered are: demand profiles, weather profiles and
# prices profiles (if necessary). demand profiles are stored in buildings
# and other information are stored in Environment objects.
# project.time_cluster(save_cls='12day_24hour.csv')
project.time_cluster(read_cls='12day_24hour.csv')

# After clustering need to update the demand profiles and storage assumptions.
for bld in project.building_list:
    bld.update_components(project.cluster)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='annual_cost')
# project.run_optimization('gurobi', save_lp=True, save_result=False)

# save model
lp_model_path = os.path.join(base_path, 'data', 'opt_output',
                             project.name + '_model.lp')
project.model.write(lp_model_path, io_options={'symbolic_solver_labels': True})

################################################################################
#                                  Post-processing
################################################################################

# result_output_path = os.path.join(base_path, 'data', 'opt_output',
#                                   project.name + '_result.csv')
# # post_pro.plot_all(result_output_path, time_interval=[0, env_10.time_step])
