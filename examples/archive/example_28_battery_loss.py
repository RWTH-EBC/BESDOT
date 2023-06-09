"""
This script is a test use case for battery. The influence of the energy loss
in each time step would be analyzed.
"""

import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
from utils.post_processing import find_size, sum_flow

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project and an environment object at first.
project_1 = Project(name='project_28_no_loss', typ='building')
project_2 = Project(name='project_28_with_loss', typ='building')
env = Environment(time_step=8760)
# Change the price of electricity and feed in price to make the battery
# profitable.
env.elec_price = 0.5
env.elec_feed_price = 0.02

project_1.add_environment(env)
project_2.add_environment(env)

# Two buildings object are generated. In building 1 the loss of battery is
# not considered, while in building 2 it is added by using another data csv
# for battery. Other attribution for both building are same.
# Make the solar area very large to generate much more electricity so that
# battery would be chosen.
bld_1 = Building(name='bld_1', area=200, solar_area=100)
bld_2 = Building(name='bld_2', area=200, solar_area=100)

# Add the energy demand profiles to the building object
bld_1.add_thermal_profile('heat', env)
bld_1.add_elec_profile(env.year, env)
bld_2.add_thermal_profile('heat', env)
bld_2.add_elec_profile(env.year, env)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file_no_loss = os.path.join(base_path, 'data', 'topology',
                                 'basic_no_loss.csv')
topo_file_with_loss = os.path.join(base_path, 'data', 'topology', 'basic.csv')
bld_1.add_topology(topo_file_no_loss)
bld_2.add_topology(topo_file_with_loss)

bld_1.add_components(project_1.environment)
bld_2.add_components(project_2.environment)
project_1.add_building(bld_1)
project_2.add_building(bld_2)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project_1.build_model()
project_1.run_optimization('gurobi', save_lp=True, save_result=True)
project_2.build_model()
project_2.run_optimization('gurobi', save_lp=True, save_result=True)

################################################################################
#                                  Post-processing
################################################################################
no_loss_result_file = os.path.join(base_path, 'data', 'opt_output',
                                   'project_28_no_loss_result.csv')
with_loss_result_file = os.path.join(base_path, 'data', 'opt_output',
                                     'project_28_with_loss_result.csv')
print('The size of project without loss:')
find_size(no_loss_result_file)

print('The size of porject with loss:')
find_size(with_loss_result_file)

print('#################')

print('The total input energy in battery without loss:')
sum_flow(no_loss_result_file, 'input_elec_bat')
print('The total output energy in battery without loss:')
sum_flow(no_loss_result_file, 'output_elec_bat')

print("Attention!, The difference between input energy and output energy is "
      "caused by the charging efficiency and discharging efficiency with 99%.")

print('The total input energy in battery with loss:')
sum_flow(with_loss_result_file, 'input_elec_bat')
print('The total output energy in battery with loss:')
sum_flow(with_loss_result_file, 'output_elec_bat')
