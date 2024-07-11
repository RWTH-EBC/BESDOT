"""
This example shows the process for building an optimization model with the
part load operation constraints of the building components (gas boiler, etc.).
"""

import os
import numpy as np
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
from scripts.components.GasBoiler import GasBoiler
from scripts.components.HeatPump import HeatPump


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
prj = Project(name='project_2', typ='building')

# Generate the environment object
env = Environment(time_step=8760, city='Dusseldorf')
prj.add_environment(env)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_2 = Building(name='bld_2', area=500, bld_typ='Multi-family house')

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
bld_2.add_thermal_profile('heat', env)
bld_2.add_hot_water_profile(env)
bld_2.add_elec_profile(env)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'basic_with_dhw.csv')
bld_2.add_topology(topo_file)
bld_2.add_components(prj.environment)
prj.add_building(bld_2)

################################################################################
#       Set the part load constraints for the gas boiler and heat pump
################################################################################
# Search for the gas boiler and heat pump components in the building
# components, and set the minimal part load coefficient to 0.3. The
# constraint would be added to the optimization model automatically. The
# component could also be found with the component name.
for item in bld_2.components:
    if isinstance(bld_2.components[item], GasBoiler) or \
            isinstance(bld_2.components[item], HeatPump):
        bld_2.components[item].min_part_load = 0.3

################################################################################
#                        Pre-Processing for time clustering
################################################################################
# The profiles could be clustered are: demand profiles, weather profiles and
# prices profiles (if necessary). demand profiles are stored in buildings
# and other information are stored in Environment objects.
# prj.time_cluster(nr_periods=15, save_cls='15day_24hour.csv')
prj.time_cluster(read_cls='15day_24hour.csv')

# After clustering need to update the demand profiles and storage assumptions.
for bld in prj.building_list:
    bld.update_components(prj.cluster)

################################################################################
#                  Build optimization model and run optimization
################################################################################
prj.build_model()
prj.run_optimization('gurobi', save_lp=True, save_result=True)
