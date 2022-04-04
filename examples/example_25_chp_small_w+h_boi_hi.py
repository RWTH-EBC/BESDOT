import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
import tools.post_processing_solar_chp as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='project_25', typ='building')

# Generate the environment object
env_25 = Environment(time_step=24)
project.add_environment(env_25)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_25 = Building(name='bld_25', area=200)

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
bld_25.add_thermal_profile('heat', env_25.temp_profile_original, env_25)
bld_25.add_elec_profile(2021, env_25)
bld_25.add_hot_water_profile(env_25)
# bld_25.add_hot_water_profile_TBL(1968, env_25)

# bld_25.demand_profile['heat_demand'] = [9, 8, 0, 9, 9, 9, 9, 9, 9, 9, 0]
# bld_25.demand_profile['elec_demand'] = [0, 0, 0, 5, 4, 1, 1, 1, 1, 0, 2]
# bld_25.demand_profile['hot_water_demand'] = [9, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# Pre define the building energy system with the topology for different
# components and add components to the building.
# todo: 1 hinter 'chp_fluid_small' kann man löschen oder hinzufügen.
# (keine Auslauftemperaturanforderung)
topo_file = os.path.join(base_path, 'data', 'topology',
                         'chp_fluid_small_w+h_boi_hi.csv')
bld_25.add_topology(topo_file)
bld_25.add_components(project.environment)
project.add_building(bld_25)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='operation_cost')
project.run_optimization('gurobi', save_lp=True, save_result=True)

################################################################################
#                                  Post-processing
################################################################################

result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                  project.name + '_result.csv')
post_pro.plot_all(result_output_path, time_interval=[0, env_25.time_step])
'''
post_pro.plot_double(result_output_path, "solar_coll", "water_tes", 365, "heat"
                     , "heat")
post_pro.plot_double(result_output_path, "water_tes", "tp_val", 365, "heat",
                     "heat")
post_pro.plot_double(result_output_path, "tp_val", "e_boi", 365, "heat",
                     "heat")
post_pro.plot_double(result_output_path, "e_boi", "hw_cns", 365, "heat",
                     "heat")

post_pro.plot_double_24h(result_output_path, "solar_coll", "water_tes")
post_pro.plot_double_24h(result_output_path, "water_tes", "tp_val")
post_pro.plot_double_24h(result_output_path, "tp_val", "e_boi")
post_pro.plot_double_24h(result_output_path, "e_boi", "hw_cns")
'''
post_pro.print_size(result_output_path)
post_pro.plot_one_line(result_output_path, 'therm_eff_chp', 'Efficiency of CHP',
                       r'Efficiency', 1.05)
post_pro.plot_two_lines(result_output_path, 'input_elec_e_grid',
                         'output_elec_e_grid', 'Input', 'Output',
                         'Profile of E-grid',
                         r'Power (kW)', 1.05)
post_pro.plot_two_lines(result_output_path, 'inlet_temp_chp',
                         'outlet_temp_chp', 'Inlet', 'Outlet',
                         'Temperature of E-grid',
                         r'Temperature ($^\circ$C)', 1.05)
post_pro.plot_four_lines(result_output_path, 'output_heat_chp',
                          'output_heat_boi', 'input_heat_hw_cns',
                          'input_heat_therm_cns', 'Heat of CHP',
                          'Heat of Boiler', 'Heat Demand', 'Hot Water Demand',
                          'Energy ', r'Power (kW)', 1.05)
