"""
This script is used to optimize the paderborn project.
"""

import os
import pandas as pd
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
from scripts.components.HeatGrid import HeatGrid

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='paderborn_neu_6_001_2', typ='building')

# Generate the environment object, which contains the weather data and price
# data.
env = Environment(time_step=8760, city='Paderborn', year=2021)
env.gas_price = 0.068
env.elec_price = 0.03  # 1: 0.3, 2: 0.75
env.biomass_price = 0.017
env.heat_price = 0.01  # 1: 0.025, 2: 0.02, 3: 0.03
# env.heat_price = 0.001
project.add_environment(env)

# If the objective of the project is the optimization for building, a building
# should be added to the project. The building object represents the three
# building in the paderborn project. The area of the building makes no
# difference for the optimization. Because the optimization is based on the
# energy demand, which is given from input data.
bld = Building(name='bld', area=2000)

# Add the energy demand profiles to the building object
heat_hotwater_file = os.path.join(base_path, 'data', 'opt_input',
                                'heat_demand_hotwater.xlsx')
heatwater_demand = pd.read_excel(heat_hotwater_file, index_col=None,
                                 header=None)
bld.demand_profile['heat_demand'] = heatwater_demand[0].tolist()
# no electricity demand for the building is considered.
elec_demand = [0] * 8760
bld.demand_profile['elec_demand'] = elec_demand

heat_steam_file = os.path.join(base_path, 'data', 'opt_input',
                                'heat_demand_steam.xlsx')
steam_demand = pd.read_excel(heat_steam_file, index_col=None, header=None)


# Pre define the building energy system with the topology for different
# components and add components to the building.
# topo_file = os.path.join(base_path, 'data', 'topology', 'paderborn_1.csv')
# topo_file = os.path.join(base_path, 'data', 'topology', 'paderborn_2.csv')
# topo_file = os.path.join(base_path, 'data', 'topology', 'paderborn_3.csv')
topo_file = os.path.join(base_path, 'data', 'topology', 'paderborn_4.csv')
# topo_file = os.path.join(base_path, 'data', 'topology', 'paderborn_5.csv')
bld.add_topology(topo_file)
bld.add_components(project.environment)

# Add the heat source profile to the heat grid component. The heat source
# profile is the unit of MW. The heat grid component will convert it to the
# unit of kW.
heat_source_file = os.path.join(base_path, 'data', 'opt_input',
                                'heat_source_heidelberg_MW.xlsx')
heat_source = pd.read_excel(heat_source_file, index_col=None, header=None)
# heat_source = (heat_source * 1000).values.tolist()
heat_source = heat_source.applymap(lambda x: x * 1000)
# print(heat_source)
for item in bld.components:
    if isinstance(bld.components[item], HeatGrid):
        bld.components[item].source_profile = heat_source[0].tolist()
for item in bld.components:
    if bld.components[item].name == 'steam_cns':
        bld.components[item].consum_profile = steam_demand[0].tolist()

project.add_building(bld)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model()

# add optional constraints
gas_heat = project.model.find_component('output_heat_hyb_boi')
# ele_heat = project.model.find_component('output_heat_e_boi')
project.model.cons.add(sum(gas_heat[t+1] for t in range(8760)) <= 3769253)

project.run_optimization('gurobi', save_lp=True, save_result=True)

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
