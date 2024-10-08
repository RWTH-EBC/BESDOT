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
prj = Project(name='project_1', typ='building')

# Generate the environment object, which contains the weather data and price
# data. If no weather file and city is given, the default weather file of
# Dusseldorf is used.
env = Environment(time_step=8760, city='Dusseldorf')
prj.add_environment(env)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_1 = Building(name='bld_1', area=500, bld_typ='Multi-family house')

# Add the energy demand profiles to the building object
bld_1.add_thermal_profile('heat', env)
bld_1.add_hot_water_profile(env)
bld_1.demand_profile['heat_demand'] = np.array(bld_1.demand_profile[
    'heat_demand']) + np.array(bld_1.demand_profile['hot_water_demand'])
bld_1.add_elec_profile(env)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
bld_1.add_topology(topo_file)
bld_1.add_components(prj.environment)
prj.add_building(bld_1)

################################################################################
#                  Build optimization model and run optimization
################################################################################
prj.build_model()
prj.run_optimization('gurobi', save_lp=True, save_result=True)

# save model. If only the optimization model is wanted, could use the
# following codes to save the model file. Other model formate like gms,
# mps are also allowed.
# lp_model_path = os.path.join(base_path, 'data', 'opt_output',
#                              test_project.name + '_model.lp')
# test_project.model.write(lp_model_path,
#                          io_options={'symbolic_solver_labels': True})
