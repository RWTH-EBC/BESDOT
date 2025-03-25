"""
This script is an example for the class project, which shows the process for
building an optimization model.
In This example the energy components are modeled with energy flow
relationship, which is provided by most other optimization utils.
"""

import os
import numpy as np
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
prj = Project(name='prj_9', typ='building')

# Generate the environment object, which contains the weather data and price
# data. If no weather file and city is given, the default weather file of
# Dusseldorf is used.
env = Environment(time_step=8760, city='Dusseldorf')
prj.add_environment(env)

# The area and bld_typ for energy hub are not necessary, but they are used to
# generate the building object.
hub = Building(name='energy_hub', area=500, solar_area=1000,
               bld_typ='Multi-family house')

# Dummy data for the energy demand profiles
# todo: replace with real data in district heating network
dhn_profile = [100] * 8760

# Add the energy demand profiles to the building object
hub.demand_profile['heat_demand'] = dhn_profile


# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'hub.csv')
hub.add_topology(topo_file)
hub.add_components(prj.environment)
prj.add_building(hub)

################################################################################
#                  Build optimization model and run optimization
################################################################################
prj.build_model()
prj.run_optimization('gurobi', save_lp=True, save_result=True)

# todo: if the revenue of the energy hub is considered, the revenue could be
#  calculated after the optimization with the total heat demand and the heat
#  price.

