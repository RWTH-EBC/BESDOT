# The combination of cluster and subsidy is not tested yet.
import os
from scripts.Project import Project
from scripts.Building import Building
from scripts.Environment import Environment
from utils.get_subsidy import find_subsidies


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
test_project = Project(name='project_9', typ='building')

# Generate the environment object, which contains the weather data and price
# data. If no weather file and city is given, the default weather file of
# Dusseldorf is used.
test_env_1 = Environment(time_step=8760, city='Dusseldorf')
test_project.add_environment(test_env_1)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
test_bld_1 = Building(name='bld_1', area=200)

# Add the energy demand profiles to the building object
test_bld_1.add_thermal_profile('heat', test_env_1)
test_bld_1.add_elec_profile(test_env_1.year, test_env_1)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_1.add_topology(topo_file)
test_bld_1.add_components(test_project.environment)

# Find out all the subsidy options for the building
subsidy_df = find_subsidies(test_env_1.city, test_env_1.state,
                            building='Neubau')
test_bld_1.add_subsidy(subsidy_df, building='Neubau')
test_project.add_building(test_bld_1)

# ################################################################################
# #                        Build pyomo model and run optimization
# ################################################################################
test_project.build_model()
test_project.run_optimization('gurobi', save_lp=True, save_result=True)