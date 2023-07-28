import os
import time
import csv
import pandas as pd
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building

for i in range(1, 13):
    for j in ['a']:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        test_env = Environment(time_step=8760)

        topo_file_1 = os.path.join(base_path, 'data', 'topology', 'basic_modi_dpm_2',
                                   f'{j}_basic_project_{i}_0_dpm_2.csv')
        topo_file_2 = os.path.join(base_path, 'data', 'topology', 'basic_modi_dpm_2',
                                   f'{j}_basic_project_{i}_1_dpm_2.csv')
        topo_file_3 = os.path.join(base_path, 'data', 'topology', 'basic_modi_dpm_2',
                                   f'{j}_basic_project_{i}_2_dpm_2.csv')

        results_file_path = os.path.join(base_path, 'data', 'opt_output', 'results_dpm_2', f'{j}_results_{i}.csv')

        # Read the data from the source file
        df = pd.read_csv(results_file_path)

        # 写入CSV文件的标题行（只在第一次时写入）
        if not os.path.isfile(results_file_path):
            with open(results_file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                component_names = ['heat_pump_size', 'therm_cns_size', 'water_tes_size', 'pv_size', 'solar_coll_size',
                                   'bat_size', 'e_grid_size', 'gas_grid_size', 'boi_size', 'e_boi_size', 'e_cns_size']
                writer.writerow(['project_name', 'total_cost', 'time_taken'] + component_names)


        def write_to_csv(project_name, total_cost, time_taken, component_sizes):
            with open(results_file_path, 'a', newline='') as csvfile_1:
                writer_1 = csv.writer(csvfile_1)
                writer_1.writerow([project_name, total_cost, time_taken] + list(component_sizes.values()))

        # Cost model 0: only with unit cost
        project_1 = Project(name=f'{j}_project_{i}_0_dpm_2', typ='building')
        project_1.add_environment(test_env)

        test_bld_1 = Building(name='bld_1', area=200, bld_typ='Verwaltungsgebäude')
        test_bld_1.add_thermal_profile('heat', test_env)
        test_bld_1.add_elec_profile(test_env.year, test_env)

        topo_file = topo_file_1
        test_bld_1.add_topology(topo_file_1)
        test_bld_1.add_components(test_env)
        project_1.add_building(test_bld_1)

        components = ['heat_pump', 'water_tes', 'boi', 'e_boi', 'solar_coll', 'pv', 'bat']
        for component in components:
            test_bld_1.components[component].change_cost_model(new_cost_model=2)

        for comp in test_bld_1.components.values():
            comp.show_cost_model()

        project_1.build_model()
        start_time = time.time()
        project_1.run_optimization('gurobi', save_lp=True, save_result=True, save_folder=f'{j}_project')
        end_time = time.time()
        time_taken_project_1 = end_time - start_time
        total_cost_project_1 = project_1.model.obj()
        component_sizes_project_1 = {}
        for comp_name, comp in test_bld_1.components.items():
            size = project_1.model.find_component('size_' + comp_name).value
            print(f"{comp_name}: size = {size}")
            component_sizes_project_1[comp_name] = size

        write_to_csv(f'{j}_project_{i}_0_dpm_2', total_cost_project_1, time_taken_project_1,
                     component_sizes_project_1)

        print("===========================================")

        ################################################################################
        #                   Cost model 1: some components has fixed cost
        ################################################################################
        project_2 = Project(name=f'{j}_project_{i}_1_dpm_2', typ='building')
        project_2.add_environment(test_env)

        test_bld_2 = Building(name='bld_2', area=200, bld_typ='Verwaltungsgebäude')
        test_bld_2.add_thermal_profile('heat', test_env)
        test_bld_2.add_elec_profile(test_env.year, test_env)

        topo_file = topo_file_2
        test_bld_2.add_topology(topo_file_2)
        test_bld_2.add_components(test_env)
        project_2.add_building(test_bld_2)

        print(test_bld_2.components.keys())

        components = ['heat_pump', 'water_tes', 'boi', 'e_boi', 'solar_coll', 'pv', 'bat']
        for component in components:
            test_bld_2.components[component].change_cost_model(new_cost_model=2)

        for comp in test_bld_2.components.values():
            comp.show_cost_model()

        project_2.build_model()
        start_time = time.time()
        project_2.run_optimization('gurobi', save_lp=True, save_result=True, save_folder=f'{j}_project')
        end_time = time.time()
        time_taken_project_2 = end_time - start_time
        total_cost_project_2 = project_2.model.obj()
        component_sizes_project_2 = {}
        for comp_name, comp in test_bld_2.components.items():
            size = project_2.model.find_component('size_' + comp_name).value
            print(f"{comp_name}: size = {size}")
            component_sizes_project_2[comp_name] = size

        write_to_csv(f'{j}_project_{i}_1_dpm_2', total_cost_project_2, time_taken_project_2,
                     component_sizes_project_2)

        print("===========================================")

        ################################################################################
        #                 Cost model 2: some components has price pairs
        ################################################################################
        project_3 = Project(name=f'{j}_project_{i}_2_dpm_2', typ='building')
        project_3.add_environment(test_env)

        test_bld_3 = Building(name='bld_3', area=200, bld_typ='Verwaltungsgebäude')
        test_bld_3.add_thermal_profile('heat', test_env)
        test_bld_3.add_elec_profile(test_env.year, test_env)

        topo_file = topo_file_3
        test_bld_3.add_topology(topo_file_3)
        test_bld_3.add_components(test_env)
        project_3.add_building(test_bld_3)

        print(test_bld_3.components.keys())

        components = ['heat_pump', 'water_tes', 'boi', 'e_boi', 'solar_coll', 'pv', 'bat']
        for component in components:
            test_bld_3.components[component].change_cost_model(new_cost_model=2)

        for comp in test_bld_3.components.values():
            comp.show_cost_model()

        project_3.build_model()
        start_time = time.time()
        project_3.run_optimization('gurobi', save_lp=True, save_result=True, save_folder=f'{j}_project')
        end_time = time.time()
        time_taken_project_3 = end_time - start_time
        total_cost_project_3 = project_3.model.obj()
        component_sizes_project_3 = {}
        for comp_name, comp in test_bld_3.components.items():
            size = project_3.model.find_component('size_' + comp_name).value
            print(f"{comp_name}: size = {size}")
            component_sizes_project_3[comp_name] = size

        write_to_csv(f'{j}_project_{i}_2_dpm_2', total_cost_project_3, time_taken_project_3,
                     component_sizes_project_3)

        print("===============================")

        for comp_name, comp in test_bld_1.components.items():
            size = project_1.model.find_component('size_' + comp_name).value
            print(f"{comp_name}: size = {size}")
        print(f"Time taken for cost_model_0: {time_taken_project_1:.2f} seconds")

        print("===========================")

        for comp_name, comp in test_bld_1.components.items():
            size = project_2.model.find_component('size_' + comp_name).value
            print(f"{comp_name}: size = {size}")
        print(f"Time taken for cost_model_1: {time_taken_project_2:.2f} seconds")

        print("===========================")

        for comp_name, comp in test_bld_1.components.items():
            size = project_3.model.find_component('size_' + comp_name).value
            print(f"{comp_name}: size = {size}")
        print(f"Time taken for cost_model_2: {time_taken_project_3:.2f} seconds")

        print("===========================")

        total_cost_project_1 = project_1.model.obj()
        total_cost_project_2 = project_2.model.obj()
        total_cost_project_3 = project_3.model.obj()

        print(f"Total cost for cost_model_0: {total_cost_project_1}")
        print(f"Total cost for cost_model_1: {total_cost_project_2}")
        print(f"Total cost for cost_model_2: {total_cost_project_3}")

        print("===========================================")

        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 读取原始结果文件
        results_file_path = os.path.join(base_path, 'data', 'opt_output', 'results_dpm_2', f'{j}_results_{i}.csv')
        df_results = pd.read_csv(results_file_path)

        # 按指定顺序重新排列数据
        project_order = [f'{j}_project_{i}_0', f'{j}_project_{i}_0_dpm_2',
                         f'{j}_project_{i}_1', f'{j}_project_{i}_1_dpm_2',
                         f'{j}_project_{i}_2', f'{j}_project_{i}_2_dpm_2']
        df_results_sorted = df_results.sort_values(by=['project_name'],
                                                   key=lambda x: x.map({p: k for k, p in enumerate(project_order)}))

        # 将重新排列后的结果保存到新的文件
        results_reordered_file_path = os.path.join(base_path, 'data', 'opt_output', 'results_dpm_2',
                                                   f'{j}_results_{i}_sorted.csv')
        df_results_sorted.to_csv(results_reordered_file_path, index=False)
