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

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


env = Environment(time_step=8760, city='Dusseldorf')

################################################################################
#                         Cost model 0: only with unit cost
################################################################################

# # Generate a project object at first.
# project_1 = Project(name='project_3_0', typ='building')
# project_1.add_environment(env)
#
# bld_1 = Building(name='bld_1', area=500, bld_typ='Multi-family house')
# bld_1.add_thermal_profile('heat', env)
# bld_1.add_hot_water_profile(env)
# # bld_1.demand_profile['heat_demand'] = np.array(bld_1.demand_profile[
# #     'heat_demand']) + np.array(bld_1.demand_profile['hot_water_demand'])
# bld_1.add_elec_profile(env)
#
# topo_file = os.path.join(base_path, 'data', 'topology', 'basic_with_dhw.csv')
# bld_1.add_topology(topo_file)
# bld_1.add_components(env)
# project_1.add_building(bld_1)
#
# # Show the cost model for each component.
# for comp in bld_1.components.values():
#     comp.show_cost_model()
#
# project_1.build_model()
# project_1.run_optimization('gurobi', save_lp=True, save_result=True)
#
# print("===========================================")
# ################################################################################
# #                   Cost model 1: some components has fixed cost
# ################################################################################
# project_2 = Project(name='project_3_1', typ='building')
# project_2.add_environment(env)
#
# bld_2 = Building(name='bld_2', area=500, bld_typ='Multi-family house')
# bld_2.add_thermal_profile('heat', env)
# bld_2.add_hot_water_profile(env)
# # bld_2.demand_profile['heat_demand'] = np.array(bld_2.demand_profile[
# #     'heat_demand']) + np.array(bld_2.demand_profile['hot_water_demand'])
# bld_2.add_elec_profile(env)
#
# topo_file = os.path.join(base_path, 'data', 'topology', 'basic_with_dhw.csv')
# bld_2.add_topology(topo_file)
# bld_2.add_components(env)
# project_2.add_building(bld_2)
#
#
# # Change the cost model for some components. Attention! Some components only
# # have unit cost, like PV. The reason is the lack of data. Most thermal
# # components have 3 cost models.
# # It could be found with component class or name, the following command is for
# # name.
# bld_2.components['heat_pump'].change_cost_model(new_cost_model=1)
# bld_2.components['water_tes'].change_cost_model(new_cost_model=1)
# bld_2.components['boi'].change_cost_model(new_cost_model=1)
# bld_2.components['e_boi'].change_cost_model(new_cost_model=1)
#
# # Show the cost model for each component.
# for comp in bld_2.components.values():
#     comp.show_cost_model()
#
# project_2.build_model()
# project_2.run_optimization('gurobi', save_lp=True, save_result=True)
#
# print("===========================================")
################################################################################
#                 Cost model 2: some components has price pairs
################################################################################
project_3 = Project(name='project_3_2_cls', typ='building')
project_3.add_environment(env)

bld_3 = Building(name='bld_3', area=500, bld_typ='Multi-family house')
bld_3.add_thermal_profile('heat', env)
bld_3.add_hot_water_profile(env)
# bld_3.demand_profile['heat_demand'] = np.array(bld_3.demand_profile[
#     'heat_demand']) + np.array(bld_3.demand_profile['hot_water_demand'])
bld_3.add_elec_profile(env)

topo_file = os.path.join(base_path, 'data', 'topology', 'basic_with_dhw.csv')
bld_3.add_topology(topo_file)
bld_3.add_components(env)
project_3.add_building(bld_3)

# Change the cost model for some components to model 2.
bld_3.components['heat_pump'].change_cost_model(new_cost_model=2)
bld_3.components['water_tes'].change_cost_model(new_cost_model=2)
bld_3.components['heat_tes'].change_cost_model(new_cost_model=2)
bld_3.components['boi'].change_cost_model(new_cost_model=2)
bld_3.components['e_boi'].change_cost_model(new_cost_model=2)

# Show the cost model for each component.
for comp in bld_3.components.values():
    comp.show_cost_model()
################################################################################
#                        Pre-Processing for time clustering
################################################################################
# The profiles could be clustered are: demand profiles, weather profiles and
# prices profiles (if necessary). demand profiles are stored in buildings
# and other information are stored in Environment objects.
# prj_2.time_cluster(nr_periods=5, save_cls='5day_24hour.csv')
# prj_2.time_cluster(nr_periods=4, save_cls='4day_24hour.csv')
# prj_2.time_cluster(nr_periods=3, save_cls='3day_24hour.csv')
project_3.time_cluster(read_cls='5day_24hour.csv')

# After clustering need to update the demand profiles and storage assumptions.
for bld in project_3.building_list:
    bld.update_components(project_3.cluster)

project_3.build_model()
project_3.run_optimization('gurobi', save_lp=False, save_result=True)
