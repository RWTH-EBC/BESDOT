import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
from scripts.subsidies.EEG import EEG
# import utils.post_processing as pp

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = Environment(time_step=8760)

# Generate project and environment object.
project_4 = Project(name='project_4_with_eeg', typ='building')
project_4.add_environment(env)

# Generate building object and connect to project.
test_bld_4 = Building(name='bld_4', area=200)
test_bld_4.add_thermal_profile('heat', env)
test_bld_4.add_elec_profile(env.year, env)

topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_4.add_topology(topo_file)
test_bld_4.add_components(env)

# Generate subsidy object EEG for PV and connect to project.
eeg = EEG()
test_bld_4.add_subsidy(eeg)
project_4.add_building(test_bld_4)

components = ['heat_pump', 'water_tes', 'boi', 'e_boi', 'solar_coll', 'pv', 'bat']
for component in components:
    test_bld_4.components[component].change_cost_model(new_cost_model=0)

for comp in test_bld_4.components.values():
    comp.show_cost_model()

project_4.build_model()
project_4.run_optimization('gurobi', save_lp=True, save_result=True, save_folder='project_4')

for comp_name, comp in test_bld_4.components.items():
    size = project_4.model.find_component('size_' + comp_name).value
    print(f"{comp_name}: size = {size}")

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
# result_file = os.path.join(base_path, 'data', 'opt_output',
#                            'project_1', 'result.csv')
# pp.find_size(result_file)
# pp.plot_all(result_file, [0, 8760])
# pp.plot_all(result_file, [624, 672],
#             save_path=os.path.join(base_path, 'data', 'opt_output',
#                                    'project_1'))
