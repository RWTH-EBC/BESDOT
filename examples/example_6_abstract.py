"""
This script is an example for the class project, which shows the process for
building an optimization model.
In This example the energy components are modeled with energy flow
relationship, which is provided by most other optimization tools.
"""

import os
from collections import OrderedDict
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
import tools.post_processing as pp

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
test_project = Project(name='project_6', typ='bilevel')

# Generate the environment object, which contains the weather data and price
# data. If no weather file and city is given, the default weather file of
# Dusseldorf is used.
test_env_1 = Environment(time_step=8760)
test_project.add_environment(test_env_1)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
test_bld_1 = Building(name='bld_6', area=200)

# Add the energy demand profiles to the building object
test_bld_1.add_thermal_profile('heat', test_env_1)
test_bld_1.add_elec_profile(test_env_1.year, test_env_1)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_1.add_topology(topo_file)
test_bld_1.add_components(test_project.environment)
test_project.add_building(test_bld_1)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
test_project.build_model()
# in test project, the built model is an AbstractModel and constraints are
# not added into the model.
data = {None: OrderedDict([('elec_price', {None: 0.32})])}
instance = test_project.model.create_instance(data=data)
test_bld_1.add_cons(instance, test_project.environment, test_project.cluster)

test_project.run_optimization('gurobi', save_lp=True, save_result=True,
                              instance=instance)

# save model. If only the optimization model is wanted, could use the
# following codes to save the model file. Other model formate like gms,
# mps are also allowed.
# lp_model_path = os.path.join(base_path, 'data', 'opt_output',
#                              test_project.name + '_model.lp')
# test_project.model.write(lp_model_path,
#                          io_options={'symbolic_solver_labels': True})

################################################################################
#                                  Post-processing
################################################################################
result_file = os.path.join(base_path, 'data', 'opt_output',
                           'project_1', 'result.csv')
# pp.find_size(result_file)
# pp.plot_all(result_file, [0, 8760])
# pp.plot_all(result_file, [624, 672],
#             save_path=os.path.join(base_path, 'data', 'opt_output',
#                                    'project_1'))
