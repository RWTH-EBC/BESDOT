"""
This example divides the heat demand of a building into two parts: one part is
space heating and the other part is hot water demand.
"""

import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='project_6', typ='building')

# Generate the environment object, which contains the weather data and price
# data.
env = Environment(time_step=8760, city='Dusseldorf')
project.add_environment(env)

# If the objective of the project is the optimization for building, a building
# should be added to the project. The building object represents the three
# building in the paderborn project. The area of the building makes no
# difference for the optimization. Because the optimization is based on the
# energy demand, which is given from input data.
bld = Building(name='bld', area=500, bld_typ='Multi-family house')

# Add the energy demand profiles to the building object
bld.add_thermal_profile('heat', env)
bld.add_hot_water_profile(env)
bld.add_elec_profile(env)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'basic_with_dhw.csv')
bld.add_topology(topo_file)
bld.add_components(project.environment)

project.add_building(bld)

################################################################################
#                        Pre-Processing for time clustering
################################################################################
# The profiles could be clustered are: demand profiles, weather profiles and
# prices profiles (if necessary). demand profiles are stored in buildings
# and other information are stored in Environment objects.
project.time_cluster(nr_periods=15, save_cls='15day_24hour.csv')
# prj.time_cluster(read_cls='15day_24hour.csv')

# After clustering need to update the demand profiles and storage assumptions.
for bld in project.building_list:
    bld.update_components(project.cluster)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model()
project.run_optimization('gurobi', save_lp=True, save_result=True)
