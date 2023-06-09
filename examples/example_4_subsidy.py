"""

"""

import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
from scripts.subsidies.EEG import EEG
import utils.post_processing as pp

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate project and environment object.
test_project = Project(name='project_4', typ='building')
test_env_4 = Environment(time_step=8760)
test_project.add_environment(test_env_4)

# Generate building object and connect to project.
test_bld_1 = Building(name='bld_4', area=200)
test_bld_1.add_thermal_profile('heat', test_env_4)
test_bld_1.add_elec_profile(test_env_4.year, test_env_4)

topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_1.add_topology(topo_file)
test_bld_1.add_components(test_project.environment)

# Generate subsidy object EEG for PV and connect to project.
eeg = EEG()
test_bld_1.add_subsidy(eeg)

test_project.add_building(test_bld_1)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
test_project.build_model()
test_project.run_optimization('gurobi', save_lp=True, save_result=True)

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
