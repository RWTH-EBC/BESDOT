"""
This example shows how to find the subsidies for a building in a specific
city and the subsidies could be used for the optimization process.
"""
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
prj = Project(name='project_4', typ='building')

# Generate the environment object, which contains the weather data and price
# data. If no weather file and city is given, the default weather file of
# Dusseldorf is used.
env_4 = Environment(time_step=8760, city='Dusseldorf')
prj.add_environment(env_4)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_4 = Building(name='bld_4', area=1000, bld_typ='Multi-family house')

# Add the energy demand profiles to the building object
bld_4.add_thermal_profile('heat', env_4)
bld_4.add_elec_profile(env_4)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
bld_4.add_topology(topo_file)
bld_4.add_components(prj.environment)

# Find out all the subsidy options for the building
# The building could be chosen from 'all', 'ExistingBuilding', 'NewBuilding'
subsidy_df = find_subsidies(env_4.city, env_4.state, building='NewBuilding')
bld_4.add_subsidy(subsidy_df, building='NewBuilding')
prj.add_building(bld_4)

################################################################################
#                Build optimization model and run optimization
################################################################################
prj.build_model()
prj.run_optimization('gurobi', save_lp=True, save_result=True)
