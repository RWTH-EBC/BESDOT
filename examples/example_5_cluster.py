"""
This example shows the temporal clustering method for optimization process,
which could reduce the calculation time and still keep the accuracy.
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
project = Project(name='project_5', typ='building')

# Generate the environment object
env = Environment(time_step=8760)
project.add_environment(env)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_5 = Building(name='bld_5', area=1000, bld_typ='Multi-family house')

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
bld_5.add_thermal_profile('heat', env)
bld_5.add_hot_water_profile(env)
bld_5.demand_profile['heat_demand'] = np.array(bld_5.demand_profile[
    'heat_demand']) + np.array(bld_5.demand_profile['hot_water_demand'])
bld_5.add_elec_profile(env)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology',
                         'basic.csv')
bld_5.add_topology(topo_file)
bld_5.add_components(project.environment)
project.add_building(bld_5)

################################################################################
#                        Pre-Processing for time clustering
################################################################################
# The profiles could be clustered are: demand profiles, weather profiles and
# prices profiles (if necessary). demand profiles are stored in buildings
# and other information are stored in Environment objects.
project.time_cluster(nr_periods=12)
# project.time_cluster(read_cls='3day_24hour.csv')

# After clustering need to update the demand profiles and storage assumptions.
for bld in project.building_list:
    bld.update_components(project.cluster)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='annual_cost')
project.run_optimization('gurobi', save_lp=True, save_result=True)

# save model
# lp_model_path = os.path.join(base_path, 'data', 'opt_output',
#                              project.name + '_model.lp')
# project.model.write(lp_model_path, io_options={'symbolic_solver_labels': True})
