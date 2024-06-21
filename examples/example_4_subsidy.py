"""
This example shows how to find the subsidies for a building in a specific
city and the subsidies could be used for the optimization process.
"""
import os
import numpy as np
from scripts.Project import Project
from scripts.Building import Building
from scripts.Environment import Environment
from utils.get_subsidy import find_subsidies


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
prj = Project(name='project_4_1', typ='building')

# Generate the environment object, which contains the weather data and price
# data. If no weather file and city is given, the default weather file of
# Dusseldorf is used.
env_4 = Environment(time_step=8760, city='Dusseldorf')
prj.add_environment(env_4)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_4 = Building(name='bld_4_1', area=500, bld_typ='Multi-family house')

# Add the energy demand profiles to the building object
bld_4.add_thermal_profile('heat', env_4)
bld_4.add_hot_water_profile(env_4)
# bld_4.demand_profile['heat_demand'] = np.array(bld_4.demand_profile[
#     'heat_demand']) + np.array(bld_4.demand_profile['hot_water_demand'])
bld_4.add_elec_profile(env_4)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'basic_with_dhw.csv')
bld_4.add_topology(topo_file)
bld_4.add_components(prj.environment)

# Change the cost model for some components to simulate the subsidy effect.
bld_4.components['heat_pump'].change_cost_model(new_cost_model=1)
bld_4.components['water_tes'].change_cost_model(new_cost_model=1)
bld_4.components['heat_tes'].change_cost_model(new_cost_model=1)
bld_4.components['boi'].change_cost_model(new_cost_model=1)
bld_4.components['e_boi'].change_cost_model(new_cost_model=1)

# Find out all the subsidy options for the building
# The building could be chosen from 'all', 'ExistingBuilding', 'NewBuilding'
subsidy_df = find_subsidies(env_4.city, env_4.state, building='NewBuilding')
bld_4.add_subsidy(subsidy_df, building='NewBuilding')
prj.add_building(bld_4)

################################################################################
#                        Pre-Processing for time clustering
################################################################################
# The profiles could be clustered are: demand profiles, weather profiles and
# prices profiles (if necessary). demand profiles are stored in buildings
# and other information are stored in Environment objects.
# prj.time_cluster(nr_periods=4, save_cls='4day_24hour.csv')
# prj.time_cluster(nr_periods=4, save_cls='4day_24hour.csv')
# prj.time_cluster(nr_periods=3, save_cls='3day_24hour.csv')
prj.time_cluster(read_cls='3day_24hour.csv')

# After clustering need to update the demand profiles and storage assumptions.
for bld in prj.building_list:
    bld.update_components(prj.cluster)
# The operation subsidies are also influenced by the clustering, so the
# subsidy should also be updated.
for bld in prj.building_list:
    bld.update_subsidy(prj.cluster)

################################################################################
#                Build optimization model and run optimization
################################################################################
prj.build_model()
prj.run_optimization('gurobi', save_lp=False, save_result=True)


################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
prj_2 = Project(name='project_4_2', typ='building')

env_5 = Environment(time_step=8760, city='Dusseldorf')
prj_2.add_environment(env_5)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_5 = Building(name='bld_4_2', area=500, bld_typ='Multi-family house')

# Add the energy demand profiles to the building object
bld_5.add_thermal_profile('heat', env_5)
bld_5.add_hot_water_profile(env_5)
bld_5.add_elec_profile(env_5)

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'basic_with_dhw.csv')
bld_5.add_topology(topo_file)
bld_5.add_components(prj_2.environment)

# Change the cost model for some components to simulate the subsidy effect.
bld_5.components['heat_pump'].change_cost_model(new_cost_model=2)
bld_5.components['water_tes'].change_cost_model(new_cost_model=2)
bld_5.components['heat_tes'].change_cost_model(new_cost_model=2)
bld_5.components['boi'].change_cost_model(new_cost_model=2)
bld_5.components['e_boi'].change_cost_model(new_cost_model=2)

# Find out all the subsidy options for the building
# The building could be chosen from 'all', 'ExistingBuilding', 'NewBuilding'
subsidy_df = find_subsidies(env_5.city, env_5.state, building='NewBuilding')
bld_5.add_subsidy(subsidy_df, building='NewBuilding')
prj_2.add_building(bld_5)

# for item in bld_5.components:
#     new_subsidy_list = []
#     for sub in bld_5.components[item].subsidy_list:
#         if sub.sub_type == 'purchase' and sub.apply_for in [
#             'Battery',
#             'SolarThermalCollector',
#             # 'PV',
#             # 'HeatPumpAirWater',
#         ]:
#             continue
#         elif sub.sub_type == 'operate':
#             continue
#         new_subsidy_list.append(sub)
#     bld_5.components[item].subsidy_list = new_subsidy_list
#     print("The subsidy for the component " + item + " is: " + str(
#         bld_5.components[item].subsidy_list))

################################################################################
#                        Pre-Processing for time clustering
################################################################################
# The profiles could be clustered are: demand profiles, weather profiles and
# prices profiles (if necessary). demand profiles are stored in buildings
# and other information are stored in Environment objects.
# prj.time_cluster(nr_periods=12, save_cls='12day_24hour.csv')
# prj.time_cluster(nr_periods=4, save_cls='4day_24hour.csv')
# prj.time_cluster(nr_periods=3, save_cls='3day_24hour.csv')
prj.time_cluster(read_cls='3day_24hour.csv')

# After clustering need to update the demand profiles and storage assumptions.
for bld in prj.building_list:
    bld.update_components(prj.cluster)
# The operation subsidies are also influenced by the clustering, so the
# subsidy should also be updated.
for bld in prj.building_list:
    bld.update_subsidy(prj.cluster)

################################################################################
#                Build optimization model and run optimization
################################################################################
prj_2.build_model()
prj_2.run_optimization('gurobi', save_lp=False, save_result=True)
