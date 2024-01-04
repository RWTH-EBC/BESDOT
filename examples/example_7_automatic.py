import os
import time
import itertools
import pandas as pd
from scripts.Project import Project
from scripts.Building import Building
from scripts.Environment import Environment


# Define a function to run optimization and obtain results for the topology file.
def run_optimization_for_topology_file(topo_file, env, project_name, cost_model):
    # Creating a project object.
    project = Project(name=project_name, typ='building')
    project.add_environment(env)

    # Creating a building object.
    bld = Building(name='bld', area=200, bld_typ='Verwaltungsgebäude')
    bld.add_thermal_profile('heat', env)
    bld.add_elec_profile(env.year, env)

    # Adding a topology file
    bld.add_topology(topo_file)
    bld.add_components(env)
    project.add_building(bld)

    # If the cost model is greater than 0, update the component's cost model
    if cost_model > 0:
        components = ['heat_pump', 'water_tes', 'boi', 'e_boi', 'solar_coll', 'pv', 'bat']
        for component in components:
            if component in bld.components:
                bld.components[component].change_cost_model(new_cost_model=cost_model)

    # build a model
    project.build_model()

    # Recording start time
    start_time = time.time()

    # run optimization
    project.run_optimization('gurobi', save_lp=True, save_result=True, save_folder='d_project')

    # Recording end time
    end_time = time.time()
    time_taken = end_time - start_time

    # Output Runtime and Total Cost
    print(f"Time taken for {project_name}: {time_taken:.2f} seconds")
    total_cost = project.model.obj()
    print(f"Total cost for {project_name}: {total_cost}")

    # Constructing the resultant data dictionary
    data = {
        'project_name': project_name,
        'total_cost': total_cost,
        'time_taken': time_taken,
    }

    # Iterate over building components and record their dimensions.
    for comp_name, comp in bld.components.items():
        size = project.model.find_component('size_' + comp_name).value
        print(f"{comp_name}: size = {size}")
        data[comp_name + '_size'] = size

    print("===========================")
    return data


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Creating an Environment Object
env = Environment(time_step=8760, city='Lindenberg')

# Defining the Component Model Dictionary
component_models = {
    'boi': ['all_brands-Gas_heating-boiler', 'all_brands-Gas_heating-therme'],
    'water_tes': ['all_brands-Storage_technology-buffer_storage-0_Heat_exchanger',
                  'all_brands-Storage_technology-buffer_storage-1_Heat_exchanger',
                  'all_brands-Storage_technology-buffer_storage-2_Heat_exchanger'],
    'solar_coll': ['all_brands-Solar_technology-flat-plate_collectors',
                   'all_brands-Solar_technology-tube_collectors']
}

# Read the original topology file
original_topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
original_df = pd.read_csv(original_topo_file)

# Get the list of component models
boi_models = component_models['boi']
water_tes_models = component_models['water_tes']
solar_coll_models = component_models['solar_coll']

# Initialize Counter
counter = 1

# Iterate over all combinations of component models.
for boi_model, water_tes_model, solar_coll_model in itertools.product(boi_models,
                                                                      water_tes_models,
                                                                      solar_coll_models):

    # Create a copy of the topology file and update the model
    # names in the topology file based on the component models.
    df = original_df.copy()
    df.loc[df['comp_name'] == 'boi', 'model'] = boi_model
    df.loc[df['comp_name'] == 'water_tes', 'model'] = water_tes_model
    df.loc[df['comp_name'] == 'solar_coll', 'model'] = solar_coll_model

    # Make sure the destination folder exists.
    result_output_folder = os.path.join(base_path, 'data', 'topology', 'basic_neu')
    if not os.path.exists(result_output_folder):
        os.makedirs(result_output_folder)

    # Save the new topology file.
    new_file = os.path.join(base_path, 'data', 'topology', 'basic_neu', f'basic_{counter}.csv')
    df.to_csv(new_file, index=False)

    # Creating a results dataframe.
    results_df = pd.DataFrame()

    # For each cost model, run the optimization and obtain results.
    for cost_model in range(3):
        for i in ['d']:
            data = run_optimization_for_topology_file(new_file, env,
                                                      f'{i}_project_{counter}_{cost_model}', cost_model)
            results_df = results_df.append(data, ignore_index=True)

        # Make sure the target folder exists.
        result_output_folder = os.path.join(base_path, 'data', 'opt_output', 'results_dpm_2')
        if not os.path.exists(result_output_folder):
            os.makedirs(result_output_folder)

        # Save the resultant data frame as a CSV file.
        results_df.to_csv(os.path.join(base_path, 'data', 'opt_output', 'results_dpm_2', f'{i}_results_{counter}.csv'),
                          index=False)

    # Increase the counter value.
    counter += 1
