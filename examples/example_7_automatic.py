import os
import time
import itertools
import pandas as pd
from scripts.Project import Project
from scripts.Building import Building
from scripts.Environment import Environment


# 定义一个函数，用于为拓扑文件运行优化并获取结果
def run_optimization_for_topology_file(topo_file, env, project_name, cost_model):
    # 创建项目对象
    project = Project(name=project_name, typ='building')
    project.add_environment(env)

    # 创建建筑对象
    bld = Building(name='bld', area=200, bld_typ='Verwaltungsgebäude')
    bld.add_thermal_profile('heat', env)
    bld.add_elec_profile(env.year, env)

    # 添加拓扑文件
    bld.add_topology(topo_file)
    bld.add_components(env)
    project.add_building(bld)

    # 如果成本模型大于0，则更新组件的成本模型
    if cost_model > 0:
        components = ['heat_pump', 'water_tes', 'boi', 'e_boi', 'solar_coll', 'pv', 'bat']
        for component in components:
            if component in bld.components:
                bld.components[component].change_cost_model(new_cost_model=cost_model)

    # 构建模型
    project.build_model()

    # 记录开始时间
    start_time = time.time()

    # 运行优化
    project.run_optimization('gurobi', save_lp=True, save_result=True, save_folder='d_project')

    # 记录结束时间
    end_time = time.time()
    time_taken = end_time - start_time

    # 输出运行时间和总成本
    print(f"Time taken for {project_name}: {time_taken:.2f} seconds")
    total_cost = project.model.obj()
    print(f"Total cost for {project_name}: {total_cost}")

    # 构建结果数据字典
    data = {
        'project_name': project_name,
        'total_cost': total_cost,
        'time_taken': time_taken,
    }

    # 遍历建筑组件并记录其尺寸
    for comp_name, comp in bld.components.items():
        size = project.model.find_component('size_' + comp_name).value
        print(f"{comp_name}: size = {size}")
        data[comp_name + '_size'] = size

    print("===========================")
    return data


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建环境对象
env = Environment(time_step=8760, city='Lindenberg')

# 定义组件模型字典
component_models = {
    'boi': ['all_brands-Gas_heating-boiler', 'all_brands-Gas_heating-therme'],
    'water_tes': ['all_brands-Storage_technology-buffer_storage-0_Heat_exchanger',
                  'all_brands-Storage_technology-buffer_storage-1_Heat_exchanger',
                  'all_brands-Storage_technology-buffer_storage-2_Heat_exchanger'],
    'solar_coll': ['all_brands-Solar_technology-flat-plate_collectors',
                   'all_brands-Solar_technology-tube_collectors']
}

# 读取原始拓扑文件
original_topo_file = os.path.join(base_path, 'data', 'topology', 'basic.csv')
original_df = pd.read_csv(original_topo_file)

# 获取组件模型列表
boi_models = component_models['boi']
water_tes_models = component_models['water_tes']
solar_coll_models = component_models['solar_coll']

# 初始化计数器
counter = 1

# 遍历所有组件模型的组合
for boi_model, water_tes_model, solar_coll_model in itertools.product(boi_models,
                                                                      water_tes_models,
                                                                      solar_coll_models):

    # 创建拓扑文件的副本，并根据组件模型更新拓扑文件中的模型名称
    df = original_df.copy()
    df.loc[df['comp_name'] == 'boi', 'model'] = boi_model
    df.loc[df['comp_name'] == 'water_tes', 'model'] = water_tes_model
    df.loc[df['comp_name'] == 'solar_coll', 'model'] = solar_coll_model

    # 确保目标文件夹存在
    result_output_folder = os.path.join(base_path, 'data', 'topology', 'basic_neu')
    if not os.path.exists(result_output_folder):
        os.makedirs(result_output_folder)

    # 保存新的拓扑文件
    new_file = os.path.join(base_path, 'data', 'topology', 'basic_neu', f'basic_{counter}.csv')
    df.to_csv(new_file, index=False)

    # 创建结果数据框
    results_df = pd.DataFrame()

    # 对于每种成本模型，运行优化并获取结果
    for cost_model in range(3):
        for i in ['d']:
            data = run_optimization_for_topology_file(new_file, env,
                                                      f'{i}_project_{counter}_{cost_model}', cost_model)
            results_df = results_df.append(data, ignore_index=True)

        # 确保目标文件夹存在
        result_output_folder = os.path.join(base_path, 'data', 'opt_output', 'results_dpm_2')
        if not os.path.exists(result_output_folder):
            os.makedirs(result_output_folder)

        # 保存结果数据框为CSV文件
        results_df.to_csv(os.path.join(base_path, 'data', 'opt_output', 'results_dpm_2', f'{i}_results_{counter}.csv'),
                          index=False)

    # 增加计数器的值
    counter += 1
