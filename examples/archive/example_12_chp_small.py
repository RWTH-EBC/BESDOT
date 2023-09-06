import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
# import utils.post_solar_chp as post_pro


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project = Project(name='project_12', typ='building')

env_12 = Environment(time_step=8760, city='Aachen')
project.add_environment(env_12)

bld_12 = Building(name='bld_12', area=200, bld_typ='Wohngebäude')
bld_12.demand_profile['heat_demand'] = [10, 10, 10, 10, 0, 10, 10, 10]
bld_12.demand_profile["elec_demand"] = [0, 0, 0]*10

topo_file = os.path.join(base_path, '..', 'data', 'topology', 'chp_fluid_small.csv')
bld_12.add_topology(topo_file)
bld_12.add_components(project.environment)
project.add_building(bld_12)

components = ['water_tes', 'chp', 'tp_val']
for component in components:
    bld_12.components[component].change_cost_model(new_cost_model=0)

for comp in bld_12.components.values():
    comp.show_cost_model()

project.build_model()
project.run_optimization('gurobi', save_lp=True, save_result=True, save_folder='project_4')

for comp_name, comp in bld_12.components.items():
    size = project.model.find_component('size_' + comp_name).value
    print(f"{comp_name}: size = {size}")
