"""
This script is used to validate Homostorage class with the annual cost. To
Check if the right size of Storage could be choose.
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
project = Project(name='project_2_2', typ='building')

# Generate the environment object
env_2_2 = Environment()
project.add_environment(env_2_2)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_2 = Building(name='bld_2_2', area=200)

# Add the energy demand profiles to the building object
# Manual add special thermal profile to test the model
bld_2.demand_profile["heat_demand"] = [0, 1] * 4380

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology',
                         'homostorage_dimension.csv')
bld_2.add_topology(topo_file)
bld_2.add_components(project.environment)
project.add_building(bld_2)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model()
project.run_optimization('gurobi', save_lp=True, save_result=True)

################################################################################
#                                  Post-processing
################################################################################

result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                  project.name + '_result.csv')
post_pro.plot_all(result_output_path, [0, 24])
