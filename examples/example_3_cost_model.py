"""
In this example, the different cost model are compared. As in class Component
introduced, the cost model could be set into 0, 1 or 2.
Cost model can be chosen from 0, 1, 2.
The model 0 means no fixed cost is considered, the relationship between total
price and installed size is: y=m*x. y represents the total price,
x represents the installed size, and m represents the unit cost from
database. The model 1 means fixed cost is considered, the relationship is
y=m*x+n. n represents the fixed cost. Model 1 usually has much better fitting
result than model 0. But it causes the increase of number of binare variable.
The model 2 means the price pairs, each product is seen as an individual
point for optimization model, which would bring large calculation cost. But
this model is the most consistent with reality.
"""

import os
import numpy as np
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
# import utils.post_processing as pp

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


test_env = Environment(time_step=8760, city='Stuttgart')
print(max(test_env.temp_profile_whole))
print(min(test_env.temp_profile_whole))
mean_value = np.mean(test_env.temp_profile_whole)
print(mean_value)

################################################################################
#                         Cost model 0: only with unit cost
################################################################################

# Generate a project object at first.
project_1 = Project(name='project_3_0', typ='building')
project_1.add_environment(test_env)

test_bld_1 = Building(name='bld_1', area=200)
test_bld_1.add_thermal_profile('heat', test_env)
test_bld_1.add_elec_profile(test_env.year, test_env)

topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_1.add_topology(topo_file)
test_bld_1.add_components(test_env)
project_1.add_building(test_bld_1)

# Show the cost model for each component.
for comp in test_bld_1.components.values():
    comp.show_cost_model()

project_1.build_model()
project_1.run_optimization('gurobi', save_lp=True, save_result=True)

print("===========================================")
################################################################################
#                   Cost model 1: some components has fixed cost
################################################################################
project_2 = Project(name='project_3_1', typ='building')
project_2.add_environment(test_env)

test_bld_2 = Building(name='bld_2', area=200)
test_bld_2.add_thermal_profile('heat', test_env)
test_bld_2.add_elec_profile(test_env.year, test_env)

topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_2.add_topology(topo_file)
test_bld_2.add_components(test_env)
project_2.add_building(test_bld_2)

# The name of each component could be found with following command.
# print(test_bld_2.components.keys())

# Change the cost model for some components. Attention! Some components only
# have unit cost, like PV. The reason is the lack of data. Most thermal
# components have 3 cost models.
# Change the cost model need to call the component in building, so the name
# of component need to be found at first. The command in last block show the
# recommended way to get the component name.
test_bld_2.components['heat_pump'].change_cost_model(new_cost_model=1)
# test_bld_2.components['water_tes'].change_cost_model(new_cost_model=1)
# test_bld_2.components['boi'].change_cost_model(new_cost_model=1)

# Show the cost model for each component.
for comp in test_bld_2.components.values():
    comp.show_cost_model()

project_2.build_model()
project_2.run_optimization('gurobi', save_lp=True, save_result=True)

print("===========================================")
################################################################################
#                 Cost model 2: some components has price pairs
################################################################################
project_3 = Project(name='project_3_2', typ='building')
project_3.add_environment(test_env)

test_bld_3 = Building(name='bld_3', area=200)
test_bld_3.add_thermal_profile('heat', test_env)
test_bld_3.add_elec_profile(test_env.year, test_env)

topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
test_bld_3.add_topology(topo_file)
test_bld_3.add_components(test_env)
project_3.add_building(test_bld_3)

# The name of each component could be found with following command.
# print(test_bld_2.components.keys())

# Change the cost model for some components. Attention! Some components only
# have unit cost, like PV. The reason is the lack of data. Most thermal
# components have 3 cost models.
# Change the cost model need to call the component in building, so the name
# of component need to be found at first. The command in last block show the
# recommended way to get the component name.
test_bld_3.components['heat_pump'].change_cost_model(new_cost_model=2)
test_bld_3.components['water_tes'].change_cost_model(new_cost_model=2)
test_bld_3.components['boi'].change_cost_model(new_cost_model=2)

# Show the cost model for each component.
for comp in test_bld_3.components.values():
    comp.show_cost_model()

project_3.build_model()
project_3.run_optimization('gurobi', save_lp=True, save_result=True)
