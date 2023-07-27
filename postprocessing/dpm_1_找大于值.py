import os
import csv
import time
import numpy as np
import pandas as pd


def write_to_csv(data, file_path_1):
    with open(file_path_1, 'w', newline='') as csvfile:
        writer_1 = csv.writer(csvfile)
        writer_1.writerow(['project_name', 'comp_name', 'size_or', 'size_op', 'cost_op'])
        writer_1.writerows(data)


# 定义文件夹路径
base_directory = os.path.dirname(os.path.abspath(__file__))
topology_folder = os.path.join(base_directory, '..', 'data', 'topology', 'basic_neu')
component_folder = os.path.join(base_directory, '..', 'data', 'component_database')

for i in range(1, 13):
    for j in ['a', 'b', 'c', 'd']:
        component_results = []

        # 读取basic.csv文件
        basic_file = os.path.join(topology_folder, f'basic_{i}.csv')
        df_basic = pd.read_csv(basic_file)

        # 保存所有组件的"data-pair"数据
        data_strings = []

        # 遍历每个组件
        for _, row in df_basic.iterrows():
            comp_type = row['comp_type']
            comp_name = row['comp_name']
            model = row['model']

            # 根据组件名称和model找到对应的文件
            comp_folder = os.path.join(component_folder, comp_type)
            matching_files = [file for file in os.listdir(comp_folder) if file.startswith(model)]

            if len(matching_files) > 0:
                file_path = os.path.join(comp_folder, matching_files[0])

                # 读取CSV文件并提取"data-pair"列的数据
                df_comp = pd.read_csv(file_path)

                # 检查是否存在"data-pair"列
                if "data-pair" not in df_comp.columns:
                    continue

                data_str = df_comp["data-pair"].values[0]
                data_strings.append((comp_name, data_str))

            else:
                print(f"No matching file found for {comp_name} - {model}")

        # 打印所有组件的数据字符串
        for i_1, (comp_name, data_str) in enumerate(data_strings):
            # 使用 "/" 分割字符串，得到每对数据
            pairs_str = data_str.split("/")
            sizes = []
            costs = []

            # 遍历每对数据，使用 ";" 分割字符串，得到 size 和 cost
            for pair_str in pairs_str:
                size_str, cost_str = pair_str.split(";")
                sizes.append(float(size_str))
                costs.append(float(cost_str))

            file_names = ['result.csv', 'result.csv']
            base_directory = os.path.dirname(os.path.abspath(__file__))
            data_directory_0 = os.path.join(base_directory, '..', 'data', 'opt_output',
                                            f'{j}_project', f'{j}_project_{i}_0')
            data_directory_1 = os.path.join(base_directory, '..', 'data', 'opt_output',
                                            f'{j}_project', f'{j}_project_{i}_1')
            data_directories = [data_directory_0, data_directory_1]

            project_names = [f'{j}_project_{i}_0', f'{j}_project_{i}_1']

            # 定义常数用于进行单位转换
            water_heat_capacity = 4.18 * 10 ** 3  # 单位：J/kgK
            temp_difference = 60  # K
            unit_conversion = 3600 * 1000  # J/kWh
            slope_conversion = unit_conversion / (water_heat_capacity * temp_difference)

            for project_name, file_name, data_directory in zip(project_names, file_names, data_directories):
                result_file_path = os.path.join(base_directory, '..', 'data', 'opt_output',
                                                data_directory, file_name)
                df_result = pd.read_csv(result_file_path)
                target_column = f"size_{comp_name}[None]"
                x_target = df_result[df_result.iloc[:, 1] == target_column].iloc[:, 2].values[0]

                optimal_size = None
                optimal_cost = None

                if optimal_size is not None and optimal_cost is not None:
                    component_results.append([project_name, comp_name, x_target, optimal_size, optimal_cost])

                if np.isnan(x_target) or x_target == 0:
                    optimal_size = 0
                    optimal_cost = 0
                    component_results.append([project_name, comp_name, x_target, optimal_size, optimal_cost])
                    continue

                # 对于 water_tes 组件进行单位转换
                if comp_name == "water_tes":
                    x_target = round(x_target * slope_conversion)

                # 开始计时
                start_time = time.time()

                size_or = x_target

                # 找到大于给定大小值（size）的最小成本值（cost）
                valid_sizes = [size for size in sizes if size >= size_or]
                if len(valid_sizes) > 0:
                    min_cost = min(costs[sizes.index(valid_sizes[0]):])
                    size_op = sizes[costs.index(min_cost)]
                    cost_op = min_cost
                else:
                    size_op = "None"
                    cost_op = "None"

                component_results.append([project_name, comp_name, size_or, size_op, cost_op])

                # 结束计时
                end_time = time.time()

                # 计算并打印运行时间
                elapsed_time = end_time - start_time

                # 确定保存路径
                output_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                             'data', 'opt_output', 'times_taken')

                # 确保目标文件夹存在
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                # 文件路径
                filename = os.path.join(output_folder, 'optimized_times_dpm_1.csv')

                # 检查文件是否存在，如果不存在或者为空，写入标题行
                if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                    with open(filename, 'w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(['Project_Name', 'Elapsed_Time', None])

                # 将项目名和时间记录到CSV文件中
                with open(filename, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([f'{j}_project_{i}_{comp_name}_ems_1', elapsed_time])

        # 保存排序后的数据到CSV文件
        output_folder = os.path.join(base_directory, '..', 'data', 'opt_output', 'output_dpm_1')
        os.makedirs(output_folder, exist_ok=True)

        output_file_path = os.path.join(output_folder, f'{j}_component_optimal_data_{i}.csv')
        write_to_csv(component_results, output_file_path)

        # 读取CSV文件的所有数据
        df = pd.read_csv(output_file_path)

        # 按照 'comp_name' 和 'project_name' 排序
        df_sorted = df.sort_values(by=['comp_name', 'project_name'])

        # 保存排序后的数据到CSV文件
        output_folder_sorted = os.path.join(base_directory, '..', 'data', 'opt_output', 'output_dpm_1_sorted')
        os.makedirs(output_folder_sorted, exist_ok=True)

        # 将排序后的数据保存到新的CSV文件
        sorted_output_file_path = os.path.join(output_folder_sorted, f'{j}_sorted_component_optimal_data_{i}.csv')
        df_sorted.to_csv(sorted_output_file_path, index=False)

        # 创建空的DataFrame
        df_output = pd.DataFrame(columns=['component'])

        # 保存没有"data-pair"的组件
        data_strings = []

        # 遍历每个组件
        for _, row in df_basic.iterrows():
            comp_type = row['comp_type']
            comp_name = row['comp_name']
            model = row['model']

            # 根据组件名称和model找到对应的文件
            comp_folder = os.path.join(component_folder, comp_type)
            matching_files = [file for file in os.listdir(comp_folder) if file.startswith(model)]

            if len(matching_files) > 0:
                file_path = os.path.join(comp_folder, matching_files[0])

                # 读取CSV文件并提取"data-pair"列的数据
                df_comp = pd.read_csv(file_path)

                # 检查是否存在"data-pair"列
                if "data-pair" not in df_comp.columns:
                    data_strings.append(comp_name)
                    continue

            else:
                data_strings.append(comp_name)

        # 将没有"data-pair"的组件保存到DataFrame中
        df_output['component'] = data_strings

        file_names = ['result.csv', 'result.csv']
        base_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory_0 = os.path.join(base_directory, '..', 'data', 'opt_output',
                                        f'{j}_project', f'{j}_project_{i}_0')
        data_directory_1 = os.path.join(base_directory, '..', 'data', 'opt_output',
                                        f'{j}_project', f'{j}_project_{i}_1')
        data_directories = [data_directory_0, data_directory_1]

        project_names = [f'{j}_project_{i}_0',
                         f'{j}_project_{i}_1',
                         f'{j}_project_{i}_2']

        for project_name, file_name, data_directory in zip(project_names, file_names, data_directories):
            result_file_path = os.path.join(data_directory, file_name)
            df_result = pd.read_csv(result_file_path)

            for comp_name in data_strings:
                if comp_name in data_strings:
                    size_op_row = df_result[df_result.iloc[:, 1] == f'size_{comp_name}[None]']
                    cost_op_row = df_result[df_result.iloc[:, 1] == f'invest_{comp_name}[None]']

                    if size_op_row.empty or cost_op_row.empty:
                        size_op = "None"
                        cost_op = "None"
                    else:
                        size_op = size_op_row.iloc[0, 2]
                        cost_op = cost_op_row.iloc[0, 2]

                        if pd.isna(size_op):
                            size_op = "None"
                        else:
                            size_op = size_op

                        if pd.isna(cost_op):
                            cost_op = "None"
                        else:
                            cost_op = cost_op

                    component_results.append([project_name, comp_name, size_op, size_op, cost_op])

        component_list = []
        # 遍历每个组件
        for _, row in df_basic.iterrows():
            comp_name = row['comp_name']
            component_list.append(comp_name)

        file_name = 'result.csv'
        base_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(base_directory, '..', 'data', 'opt_output', f'{j}_project', f'{j}_project_{i}_2')
        project_name = f'{j}_project_{i}_2'
        result_file_path = os.path.join(data_directory, file_name)
        df_result = pd.read_csv(result_file_path)

        # 添加project_1_2中所有组件的size和invest值
        for comp_name in component_list:
            size_og_row = df_result[df_result.iloc[:, 1] == f'size_{comp_name}[None]']
            size_op_row = df_result[df_result.iloc[:, 1] == f'size_{comp_name}[None]']
            invest_op_row = df_result[df_result.iloc[:, 1] == f'invest_{comp_name}[None]']

            water_heat_capacity = 4.18 * 10 ** 3  # 单位：J/kgK
            water_density = 1  # kg/L
            temp_difference = 60  # K
            unit_conversion = 3600 * 1000  # J/kWh
            slope_conversion = unit_conversion / (water_heat_capacity * temp_difference)

            if size_og_row.empty:
                size_og = "None"
            else:
                size_og = size_og_row.iloc[0, 2]
                # 对于 water_tes 组件进行单位转换
                if comp_name == "water_tes":
                    size_og = round(size_og * slope_conversion)

            if size_op_row.empty:
                size_op = "None"
            else:
                size_op = size_op_row.iloc[0, 2]
                # 对于 water_tes 组件进行单位转换
                if comp_name == "water_tes":
                    size_op = round(size_op * slope_conversion)

            if invest_op_row.empty:
                invest_op = "None"
            else:
                invest_op = invest_op_row.iloc[0, 2]
                # 对于 water_tes 组件进行单位转换
                if comp_name == "water_tes":
                    invest_op = invest_op

            component_results.append([f'{j}_project_{i}_2', comp_name, size_og, size_op, invest_op])

        # 保存排序后的数据到CSV文件
        output_folder_1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_1')
        os.makedirs(output_folder_1, exist_ok=True)

        output_file_path = os.path.join(output_folder_1, f'{j}_component_optimal_data_{i}.csv')
        write_to_csv(component_results, output_file_path)

        # 读取CSV文件的所有数据
        df = pd.read_csv(output_file_path)

        # 按照 'comp_name' 和 'project_name' 排序
        df_sorted = df.sort_values(by=['comp_name', 'project_name'])

        # 保存排序后的数据到CSV文件
        output_folder_2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_1_sorted')
        os.makedirs(output_folder_2, exist_ok=True)

        # 将排序后的数据保存到新的CSV文件
        sorted_output_file_path = os.path.join(output_folder_2, f'{j}_sorted_component_optimal_data_{i}.csv')
        df_sorted.to_csv(sorted_output_file_path, index=False)

        print('===================================================================================================')

        # 读取原始数据文件
        output_folder_2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_1_sorted')
        input_file_path = os.path.join(output_folder_2, f'{j}_sorted_component_optimal_data_{i}.csv')
        df = pd.read_csv(input_file_path)

        # 创建必要的列
        columns_to_adds = {
            'boi': ['Hersteller', 'Modell', 'Artikelnummer', 'URL', 'Preis_UVP', 'Preis_Reduziert', 'Lieferumfang',
                    'Leistung [kW]', 'Gasart', 'Vorlauftemperatur [°C]', 'Betriebsüberdruck [bar]', 'Klasse',
                    'max Leistungsaufnahme elek. [W]', 'min Leistungsaufnahme elek. [W]',
                    'Jahreszeitbedingte Raumheizungs-Energieeffizienz [%]', 'max Normnutzungsgrad 80/60 [%]',
                    'min Normnutzungsgrad 80/60 [%]', 'max Wärmeleistung 80/60 [kW]', 'min Wärmeleistung 80/60 [kW]',
                    'max Feuerungswärmeleistung 80/60 [kW]', 'min Feuerungswärmeleistung 80/60 [kW]',
                    'max Abgastemperatur 80/60 [°C]', 'min Abgastemperatur 80/60 [°C]', 'Förderdruck 80/60 [Pa]',
                    'max Normnutzungsgrad 50/30 [%]', 'min Normnutzungsgrad 50/30 [%]', 'max Wärmeleistung 50/30 [kW]',
                    'min Wärmeleistung 50/30 [kW]', 'max Feuerungswärmeleistung 50/30 [kW]',
                    'min Feuerungswärmeleistung 50/30 [kW]',
                    'max Abgastemperatur 50/30 [°C]', 'min Abgastemperatur 50/30 [°C]', 'Förderdruck 50/30 [Pa]'],
            'water_tes': ['Hersteller', 'Modell', 'Artikelnummer', 'URL', 'Preis_UVP', 'Preis_Reduziert',
                          'Lieferumfang', 'Speicherinhalt [l]', 'Klasse', 'Bereitschaftswärmeaufwand [kWh/24h]',
                          'Heizfläche WT 1 [m²]', 'Heizfläche WT 2 [m²]', 'Volumen WT 1 [l]',
                          'Volumen WT 2 [l]', 'Betriebsüberdruck [bar]', 'Betriebstemperatur [°C]']
        }

        comp_names = ['boi', 'water_tes']

        component_files = {
            'boi': 'Gas_heating_boiler-20211230-15_33_59.csv',
            'water_tes': 'Storage_technology_buffer_storage-20220317-16_40_46.csv'
        }

        component_matching_columns = {
            'boi': 'Leistung [kW]',
            'water_tes': 'Speicherinhalt [l]'
        }

        for comp_name in comp_names:
            # 定义特定组件的 CSV 文件路径
            csv_file_path = os.path.join(output_folder_2, '../..', 'products_table', component_files[comp_name])

            # 读取特定组件的 CSV 文件数据
            df_gas = pd.read_csv(csv_file_path)

            # 添加必要的列
            columns_to_add = columns_to_adds[comp_name]
            for column in columns_to_add:
                if column not in df.columns:
                    df[column] = None

            projects = [f'{j}_project_{i}_0',
                        f'{j}_project_{i}_1',
                        f'{j}_project_{i}_2']

            for project in projects:
                try:
                    size_op = float(df.loc[(df['project_name'] == project) & (df['comp_name']
                                                                              == comp_name), 'size_op'].values[0])
                    cost_op = float(df.loc[(df['project_name'] == project) & (df['comp_name']
                                                                              == comp_name), 'cost_op'].values[0])
                except ValueError:
                    print(f"Cannot convert size_op or cost_op to float for project {project}")
                    continue

                matched_row = df_gas[(df_gas[component_matching_columns[comp_name]].round(2) == round(size_op, 2)) &
                                     (df_gas['Preis_Reduziert'].round(2) == round(cost_op, 2))]

                if not matched_row.empty:
                    matched_data = matched_row[columns_to_add].iloc[0]
                    df.loc[(df['project_name'] == project) & (df['comp_name'] == comp_name), columns_to_add]\
                        = matched_data.values

        # 保存排序后的数据到CSV文件
        output_folder_3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_1_matched')
        os.makedirs(output_folder_3, exist_ok=True)

        # 将更新后的 df DataFrame 保存到新的 CSV 文件
        matched_output_file_path = os.path.join(output_folder_3, f'{j}_matched_component_optimal_data_{i}.csv')
        df.to_csv(matched_output_file_path, index=False)

        print('================================================================================================')

        base_directory = os.path.dirname(os.path.abspath(__file__))
        basic_file_path = os.path.join(base_directory, '..', 'data', 'topology', 'basic_neu', f'basic_{i}.csv')
        output_file_path = os.path.join(base_directory, '..', 'data', 'opt_output', 'output_dpm_1_sorted',
                                        f'{j}_sorted_component_optimal_data_{i}.csv')

        df_optimal = pd.read_csv(output_file_path)
        df_basic = pd.read_csv(basic_file_path)

        new_directory = os.path.join(base_directory, '..', 'data', 'topology', 'basic_modi_dpm_1')
        os.makedirs(new_directory, exist_ok=True)

        df_basic_list = [df_basic.copy() for _ in range(len(project_names))]
        new_basic_file_paths = [f'{j}_basic_project_{i}_{j_2}_dpm_1.csv' for j_2 in range(len(project_names))]

        comp_names = component_list

        for df_basic_project, project_name, new_basic_file_path in zip(df_basic_list, project_names,
                                                                       new_basic_file_paths):
            for comp_name in comp_names:
                if comp_name in ['therm_cns', 'e_cns', 'e_grid', 'gas_grid']:
                    min_size = df_basic.loc[df_basic['comp_name'] == comp_name, 'min_size'].values[0]
                    max_size = df_basic.loc[df_basic['comp_name'] == comp_name, 'max_size'].values[0]
                else:
                    min_size = df_optimal.loc[(df_optimal['project_name'] == project_name) &
                                              (df_optimal['comp_name'] == comp_name), 'size_op'].values[0]
                    max_size = min_size

                df_basic_project.loc[df_basic_project['comp_name'] == comp_name, 'min_size'] = min_size
                df_basic_project.loc[df_basic_project['comp_name'] == comp_name, 'max_size'] = max_size

            new_basic_file_path = os.path.join(new_directory, new_basic_file_path)
            df_basic_project.to_csv(new_basic_file_path, index=False)
