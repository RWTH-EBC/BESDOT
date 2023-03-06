# Qimin Li
# Datum: 2021/12/12 15:05

import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
import tools.post_solar_chp as post_pro
import tools.plot_cluster as plot_cls

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
days = 4

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='project_25', typ='building')

# Generate the environment object
# env_27 = Environment(start_time=4329, time_step=3)
env_25 = Environment(start_time=0, time_step=8760)
project.add_environment(env_25)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_25 = Building(name='bld_25', area=200, bld_typ='Wohngebäude')

# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
# bld_27.add_thermal_profile('heat', env_27.temp_profile_original, env_27)
# bld_27.add_elec_profile(2021, env_27)
bld_25.add_thermal_profile('heat', env_25)
bld_25.add_elec_profile(env_25.year, env_25)
bld_25.add_hot_water_profile(env_25)

# Pre define the building energy system with the topology for different
# components and add components to the building.

topo_file = os.path.join(base_path, 'data', 'topology', 'chp_fluid_small_hi_solar4_all.csv')
bld_25.add_topology(topo_file)
bld_25.add_components(project.environment)
project.add_building(bld_25)

################################################################################
#                        Pre-Processing for time clustering
################################################################################
# The profiles could be clustered are: demand profiles, weather profiles and
# prices profiles (if necessary). demand profiles are stored in buildings
# and other information are stored in Environment objects.
project.time_cluster(nr_periods=days, hours_period=24, save_cls=str(days) + 'day_24hour.csv')
plot_cls.step_plot_one_line(von=0, bis=(days + 1) * 24 - 1, nr=str(days))
plot_cls.step_plot_three_lines(von=0, bis=(days + 1) * 24 - 1, nr=str(days))
# After clustering need to update the demand profiles and storage assumptions.
for bld in project.building_list:
    bld.update_components(project.cluster)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model(obj_typ='annual_cost')
project.run_optimization(solver_name='gurobi', save_lp=True, save_result=True)

################################################################################
#                                  Post-processing
################################################################################

result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                  project.name + '_result.csv')
