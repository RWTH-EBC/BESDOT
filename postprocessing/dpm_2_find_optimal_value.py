import os
import csv
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, norm


for i in range(1, 13):
    for j in ['a', 'b', 'c', 'd']:

        component_results = []


        def write_to_csv(data, file_path_1):
            with open(file_path_1, 'w', newline='') as csvfile:
                writer_1 = csv.writer(csvfile)
                writer_1.writerow(['project_name', 'comp_name', 'size_or', 'size_op', 'cost_op'])
                for row_1 in data:
                    writer_1.writerow(row_1)


        # 定义文件路径和文件夹路径
        base_directory = os.path.dirname(os.path.abspath(__file__))
        topology_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'topology', 'basic_neu')
        component_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'component_database')

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
            print(data_str)

            # 使用 "/" 分割字符串，得到每对数据
            pairs_str = data_str.split("/")

            # 创建空的列表来存储 x 值（size）和 y 值（cost）
            x_values = []
            y_values = []

            # 遍历每对数据，使用 ";" 分割字符串，得到 size 和 cost
            for pair_str in pairs_str:
                size_str, cost_str = pair_str.split(";")
                x_values.append(float(size_str))
                y_values.append(float(cost_str))

            # 根据 y_values 进行排序，并重新赋值给 x_values 和 y_values
            x_values, y_values = zip(*sorted(zip(x_values, y_values), key=lambda pair: pair[1]))

            # 将排序后的数据重新构建为数据字符串
            sorted_data_str = "/".join(["{:.1f};{:.1f}".format(x, y) for x, y in zip(x_values, y_values)])

            # 打印排序后的数据字符串
            print("Sorted data string:")
            print(sorted_data_str)

            # 计算 KDE
            kde = gaussian_kde(x_values)

            # 生成 x 的值用于绘图
            x_plot = np.linspace(min(x_values), max(x_values), 500)

            # 计算每一个 x_plot 对应的 KDE 值
            density = kde(x_plot)

            # 拟合高斯分布
            mu, std = norm.fit(x_values)

            # 计算阈值
            threshold = mu - std
            threshold_density = kde(threshold)

            # 绘图
            plt.grid()
            plt.plot(x_plot, density)

            # 通过交点处的 y 值来确定另一条线的位置
            y_intersection = kde(threshold)

            # 检查阈值线 `x=threshold` 与 KDE 曲线是否有交点
            if y_intersection <= 0:
                print("No intersection between the threshold line and the KDE curve.")

            # 绘制额外的线
            plt.axhline(y=y_intersection, color='g', linestyle='--', label='Additional Line')

            # 寻找额外交点
            extra_intersection = x_plot[np.argwhere(np.diff(np.sign(density - y_intersection)) != 0).flatten()]

            # 存储额外交点的 x 值
            x_values_extra = []

            # 绘制额外的线并获取 x 值
            for intersection in extra_intersection:
                plt.axvline(x=intersection, color='g', linestyle='--', label='Additional Line')
                x_values_extra.append(intersection)

            # 打印额外线的 x 值
            print("X values of the additional lines are:", x_values_extra)

            if len(x_values_extra) == 1:
                print("Insufficient additional intersection points found.")
                range_min = x_values[0]  # 将range_min设置为原始数据的第一个值
                range_max = x_values_extra[0]
                print("High-density range:", range_min, "-", range_max)
            else:
                # 将额外线的 x 值排序
                x_values_extra.sort()

                # 提取范围的最小值和最大值
                range_min = x_values_extra[0]
                range_max = x_values_extra[1]

                # 打印高密度区间范围
                print("High-density range:", range_min, "-", range_max)

            max_density = max(density)
            max_density_index = np.argmax(density)
            x_max_density = x_plot[max_density_index]

            print("Maximum density is", max_density)
            print("X value corresponding to the maximum density is", x_max_density)

            # 指定保存文件的文件夹路径
            save_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'diagram_density_plot_component')

            # 创建保存文件夹（如果不存在）
            os.makedirs(save_folder, exist_ok=True)

            # 保存图形
            save_path = os.path.join(save_folder, f'density_plot_component_2_{comp_name}.png')
            plt.savefig(save_path)
            plt.close()

            file_names = ['result.csv', 'result.csv']
            base_directory = os.path.dirname(os.path.abspath(__file__))
            data_directory_0 = os.path.join(base_directory, '..', 'data', 'opt_output',
                                            f'{j}_project', f'{j}_project_{i}_0')
            data_directory_1 = os.path.join(base_directory, '..', 'data', 'opt_output',
                                            f'{j}_project', f'{j}_project_{i}_1')
            data_directories = [data_directory_0, data_directory_1]

            project_names = [f'{j}_project_{i}_0', f'{j}_project_{i}_1']

            x_targets = []
            x_densities = []

            # 定义常数用于进行单位转换
            water_heat_capacity = 4.18 * 10 ** 3  # 单位：J/kgK
            water_density = 1  # kg/L
            temp_difference = 60  # K
            unit_conversion = 3600 * 1000  # J/kWh
            slope_conversion = unit_conversion / (water_heat_capacity * temp_difference)

            for project_name, file_name, data_directory in zip(project_names, file_names, data_directories):
                result_file_path = os.path.join(data_directory, file_name)
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
                    print(f"Skipping component {comp_name} in {data_directory.split('/')[-1]}"
                          f" due to zero or missing size value.")
                    continue

                # 对于 water_tes 组件进行单位转换
                if comp_name == "water_tes":
                    x_target = round(x_target * slope_conversion)

                x_density = kde(x_target)
                x_targets.append(x_target)
                x_densities.append(x_density)

            for j_1, (x_target, x_density) in enumerate(zip(x_targets, x_densities)):
                if j_1 == 0:
                    project_name = f"{j}_project_{i}_0"
                else:
                    project_name = f"{j}_project_{i}_1"
                print(f"x{j_1+1} ({project_name}):", x_target)
                print(f"Density at x_target_{j_1+1} ({project_name}) =", x_target, "is", x_density)

                # 开始计时
                start_time = time.time()

                # 1.首先判断阈值是否在高斯核密度曲线上
                if min(x_values) < threshold < max(x_values):
                    print("The threshold is on the Gaussian KDE curve.")

                    # 计算阈值对应的密度值
                    threshold_density = kde(threshold)

                    # 2.判断阈值是否在高密度区间
                    range_min = x_values_extra[0]
                    range_max = x_values_extra[1]

                    if range_min <= x_target <= range_max:
                        print("The threshold is in the high-density range.")

                        # 在高密度区间内找到所有原始数据的 size 值
                        x_values_in_high_density_range = [value for value in x_values if range_min < value < range_max]

                        # 计算原始数据的 size 值的标准差
                        x_std = np.std(x_values_in_high_density_range)
                        print("Standard deviation of x values in the high-density range:", x_std)

                        # 在原始数据中找到所有密度在 lower_limit 和 max_density 之间的 x 值
                        x_values_less_than_x = [value for value in x_values if (max_density >= kde(value)
                                                                                >= threshold_density)
                                                and (x_target - x_std) <= value <= (x_target + x_std)]
                        print("X values less than x in the density range are:", x_values_less_than_x)

                        x_values_greater_than_x = [value for value in x_values if value >= x_target]
                        print("X values greater than x in the density range are:", x_values_greater_than_x)

                        # 找离 X 点最近且价格最低的点
                        # 定义误差范围值
                        error_range_values = [0.04, 0.06, 0.08, 0.10]

                        # 存储结果的列表
                        sensitivity_results = []

                        # 遍历不同的误差范围值
                        for error_range in error_range_values:
                            # 计算误差范围
                            x_error_range = x_std * error_range

                            # 找到在误差范围内与 x 最接近的数值
                            closest_x_in_range = [val for val in x_values_less_than_x if abs(val - x_target)
                                                  <= x_error_range]
                            closest_x_price_in_range = [y_values[x_values.index(val)] for val in closest_x_in_range]

                            # 确保找到的值在误差范围内
                            if all(abs(x - x_target) <= x_error_range for x in closest_x_in_range):
                                min_cost_in_range = min(zip(closest_x_in_range, closest_x_price_in_range),
                                                        key=lambda val: val[1], default=None)
                                if min_cost_in_range is not None:
                                    closest_x, closest_x_price = min_cost_in_range
                                    print("Closest x value within the error range:", closest_x)
                                    print("Corresponding price less than x in the"
                                          " density range within the error range:")
                                    print("Size:", closest_x)
                                    print("Cost:", closest_x_price)
                                else:
                                    closest_x = None
                                    closest_x_price = None
                                    print("No corresponding price found for the"
                                          " closest x value within the error range.")
                            else:
                                closest_x = None
                                closest_x_price = None
                                print("No values within the error range.")

                            # 存储敏感度分析结果
                            sensitivity_results.append({"Error Range": error_range,
                                                        "Closest X in Range": closest_x,
                                                        "Closest X Price in Range": closest_x_price})

                        # 比较结果并选择具有最小cost的error_range_values
                        optimal_result = None
                        min_cost = float('inf')  # 初始化最小cost为正无穷大
                        for result in sensitivity_results:
                            closest_x_price = result["Closest X Price in Range"]
                            if closest_x_price is not None and closest_x_price < min_cost:
                                min_cost = closest_x_price
                                optimal_result = result

                        # 打印最佳结果
                        if optimal_result is not None:
                            if "Closest X in Range" in optimal_result:
                                print("Optimal Result:")
                                print("Error Range:", optimal_result["Error Range"])
                                print("Closest X in Range:", optimal_result["Closest X in Range"])
                                print("Closest X Price in Range:", optimal_result["Closest X Price in Range"])
                            else:
                                print("No optimal result found.")
                        else:
                            print("No optimal result found")

                        # 确保找到的值在误差范围内
                        if optimal_result is not None:
                            optimal_size = optimal_result["Closest X in Range"]
                            optimal_cost = optimal_result["Closest X Price in Range"]
                        else:
                            optimal_size = None
                            optimal_cost = None

                        # 找到比 x 大的价格最低的数值
                        if x_values_greater_than_x:
                            min_price_greater_than_x = min([(value, y_values[x_values.index(value)]) for value in
                                                            x_values_greater_than_x], key=lambda val: val[1],
                                                           default=None)

                            if min_price_greater_than_x is not None:
                                x_min_price_greater_than_x, price_min_price_greater_than_x = min_price_greater_than_x
                                print("Minimum price greater than x in the density range:")
                                print("Size:", x_min_price_greater_than_x)
                                print("Cost:", price_min_price_greater_than_x)

                                # 对比价格
                                if optimal_result is not None:
                                    closest_x = optimal_result["Closest X in Range"]
                                    closest_x_price = optimal_result["Closest X Price in Range"]
                                    if price_min_price_greater_than_x is not None:
                                        if closest_x_price is not None:
                                            if price_min_price_greater_than_x < closest_x_price:
                                                optimal_size = x_min_price_greater_than_x
                                                optimal_cost = price_min_price_greater_than_x
                                            else:
                                                optimal_size = closest_x
                                                optimal_cost = closest_x_price
                                        else:
                                            optimal_size = x_min_price_greater_than_x
                                            optimal_cost = price_min_price_greater_than_x
                                    else:
                                        if closest_x_price is not None:
                                            optimal_size = closest_x
                                            optimal_cost = closest_x_price
                                        else:
                                            optimal_size = None
                                            optimal_cost = None

                                else:
                                    optimal_size = x_min_price_greater_than_x
                                    optimal_cost = price_min_price_greater_than_x

                                component_results.append([project_name, comp_name, x_target, optimal_size,
                                                          optimal_cost])

                    # 在低密度区间
                    else:
                        print("The threshold is in the low-density range.")

                        # x小于range_min的情况
                        if x_target < range_min:
                            # 在低密度区间而且小于range_min内找到所有原始数据的 size 值
                            x_values_in_low_density_range_1 = [value for value in x_values if value < range_min]

                            # 计算原始数据的 size 值的标准差
                            x_std = np.std(x_values_in_low_density_range_1)
                            print("Standard deviation of x values in the high-density range:", x_std)

                            # 在原始数据中找到所有密度在range_min之前的 x 值
                            x_values_less_than_x = [value for value in x_values if (kde(value) <= kde(range_min)
                                                                                    and (x_target - x_std)
                                                                                    <= value <= (x_target + x_std))]
                            print("X values less than x in the density range are:", x_values_less_than_x)

                            x_values_greater_than_x = [value for value in x_values if value >= x_target]
                            print("X values greater than x in the density range are:", x_values_greater_than_x)

                            # 定义误差范围值
                            error_range_values = [0.10, 0.15, 0.20, 0.25, 0.30]

                            # 存储结果的列表
                            sensitivity_results = []

                            # 遍历不同的误差范围值
                            for error_range in error_range_values:
                                # 计算误差范围
                                x_error_range = x_std * error_range

                                # 获取误差范围的最小值和最大值
                                min_x_error_range = np.amin(x_error_range)
                                max_x_error_range = np.amax(x_error_range)

                                # 找到在误差范围内与 x 最接近的数值
                                closest_x_in_range = []
                                for val in x_values_less_than_x:
                                    if abs(val - x_target) >= min_x_error_range:
                                        closest_x_in_range.append(min_x_error_range <= abs(val - x_target))
                                    else:
                                        closest_x_in_range.append(abs(val - x_target) <= max_x_error_range)

                                closest_x_price_in_range = [y_values[i] for i, val in enumerate(x_values_less_than_x)
                                                            if closest_x_in_range[i]]

                                # 确保找到的值在误差范围内
                                if all(closest_x_in_range):
                                    min_cost_in_range = min(zip(x_values_less_than_x, closest_x_price_in_range),
                                                            key=lambda val: val[1], default=None)
                                    if min_cost_in_range is not None:
                                        closest_x, closest_x_price = min_cost_in_range
                                        print("Closest x value within the error range:", closest_x)
                                        print("Corresponding price less than x in the"
                                              " density range within the error range:")
                                        print("Size:", closest_x)
                                        print("Cost:", closest_x_price)
                                    else:
                                        closest_x = None
                                        closest_x_price = None
                                        print("No corresponding price found for"
                                              " the closest x value within the error range.")
                                else:
                                    closest_x = None
                                    closest_x_price = None
                                    print("No values within the error range.")

                                # 存储敏感度分析结果
                                sensitivity_results.append({"Closest X in Range": closest_x,
                                                            "Closest X Price in Range": closest_x_price})

                            # 比较结果并选择具有最小cost的error_range_values
                            optimal_result = None
                            min_cost = float('inf')  # 初始化最小cost为正无穷大
                            for result in sensitivity_results:
                                closest_x_price = result["Closest X Price in Range"]
                                if closest_x_price is not None and closest_x_price < min_cost:
                                    min_cost = closest_x_price
                                    optimal_result = result

                            # 打印最佳结果
                            if optimal_result is not None:
                                print("Optimal Result:")
                                print("Closest X in Range:", optimal_result["Closest X in Range"])
                                print("Closest X Price in Range:", optimal_result["Closest X Price in Range"])
                            else:
                                print("No optimal result found.")

                            # 确保找到的值在误差范围内
                            if optimal_result is not None:
                                optimal_size = optimal_result["Closest X in Range"]
                                optimal_cost = optimal_result["Closest X Price in Range"]
                            else:
                                optimal_size = None
                                optimal_cost = None

                            # 找到比 x 大的价格最低的数值
                            if x_values_greater_than_x:
                                min_price_greater_than_x = min([(value, y_values[x_values.index(value)]) for value
                                                                in x_values_greater_than_x], key=lambda val: val[1],
                                                               default=None)

                                if min_price_greater_than_x is not None:
                                    x_min_price_greater_than_x, price_min_price_greater_than_x\
                                        = min_price_greater_than_x
                                    print("Minimum price greater than x in the density range:")
                                    print("Size:", x_min_price_greater_than_x)
                                    print("Cost:", price_min_price_greater_than_x)

                                    # 对比价格
                                    if optimal_result is not None:
                                        closest_x = optimal_result["Closest X in Range"]
                                        closest_x_price = optimal_result["Closest X Price in Range"]
                                        if price_min_price_greater_than_x is not None:
                                            if closest_x_price is not None:
                                                if price_min_price_greater_than_x < closest_x_price:
                                                    optimal_size = x_min_price_greater_than_x
                                                    optimal_cost = price_min_price_greater_than_x
                                                else:
                                                    optimal_size = closest_x
                                                    optimal_cost = closest_x_price
                                            else:
                                                optimal_size = x_min_price_greater_than_x
                                                optimal_cost = price_min_price_greater_than_x
                                        else:
                                            if closest_x_price is not None:
                                                optimal_size = closest_x
                                                optimal_cost = closest_x_price
                                            else:
                                                optimal_size = None
                                                optimal_cost = None

                                    else:
                                        optimal_size = x_min_price_greater_than_x
                                        optimal_cost = price_min_price_greater_than_x

                                    component_results.append([project_name, comp_name, x_target, optimal_size,
                                                              optimal_cost])

                        # x大于range_max的情况
                        elif x_target > range_max:

                            # 在低密度区间而且大于range_max内找到所有原始数据的 size 值
                            x_values_in_low_density_range_2 = [value for value in x_values if value > range_max]

                            # 计算原始数据的 size 值的标准差
                            x_std = np.std(x_values_in_low_density_range_2)
                            print("Standard deviation of x values in the high-density range:", x_std)

                            # 在原始数据中找到所有密度在range_max之前的 x 值
                            x_values_less_than_x = [value for value in x_values if (kde(value) <= kde(range_max)
                                                                                    and (x_target - x_std)
                                                                                    <= value <= x_target + x_std)]
                            print("X values less than x in the density range are:", x_values_less_than_x)

                            x_values_greater_than_x = [value for value in x_values if value >= x_target]
                            print("X values greater than x in the density range are:", x_values_greater_than_x)

                            # 定义误差范围值
                            error_range_values = [0.02, 0.03, 0.04, 0.05, 0.06]

                            # 存储结果的列表
                            sensitivity_results = []

                            # 遍历不同的误差范围值
                            for error_range in error_range_values:
                                # 计算误差范围
                                x_error_range = x_std * error_range

                                # 找到在误差范围内与 x 最接近的数值
                                closest_x_in_range = [val for val in x_values_less_than_x if abs(val - x_target)
                                                      <= x_error_range]
                                closest_x_price_in_range = [y_values[x_values.index(val)] for val in closest_x_in_range]

                                # 确保找到的值在误差范围内
                                if all(abs(x - x_target) <= x_error_range for x in closest_x_in_range):
                                    min_cost_in_range = min(zip(closest_x_in_range, closest_x_price_in_range),
                                                            key=lambda val: val[1], default=None)
                                    if min_cost_in_range is not None:
                                        closest_x, closest_x_price = min_cost_in_range
                                        print("Closest x value within the error range:", closest_x)
                                        print("Corresponding price less than x in the"
                                              " density range within the error range:")
                                        print("Size:", closest_x)
                                        print("Cost:", closest_x_price)
                                    else:
                                        closest_x = None
                                        closest_x_price = None
                                        print("No corresponding price found for the"
                                              " closest x value within the error range.")
                                else:
                                    closest_x = None
                                    closest_x_price = None
                                    print("No values within the error range.")

                                # 存储敏感度分析结果
                                sensitivity_results.append({"Error Range": error_range,
                                                            "Closest X in Range": closest_x,
                                                            "Closest X Price in Range": closest_x_price})

                            # 比较结果并选择具有最小cost的error_range_values
                            optimal_result = None
                            min_cost = float('inf')  # 初始化最小cost为正无穷大
                            for result in sensitivity_results:
                                closest_x_price = result["Closest X Price in Range"]
                                if closest_x_price is not None and closest_x_price < min_cost:
                                    min_cost = closest_x_price
                                    optimal_result = result

                            # 打印最佳结果
                            if optimal_result is not None:
                                print("Optimal Result:")
                                print("Error Range:", optimal_result["Error Range"])
                                print("Closest X in Range:", optimal_result["Closest X in Range"])
                                print("Closest X Price in Range:", optimal_result["Closest X Price in Range"])
                            else:
                                print("No optimal result found.")

                            # 确保找到的值在误差范围内
                            if optimal_result is not None:
                                optimal_size = optimal_result["Closest X in Range"]
                                optimal_cost = optimal_result["Closest X Price in Range"]
                            else:
                                optimal_size = None
                                optimal_cost = None

                            # 找到比 x 大的价格最低的数值
                            if x_values_greater_than_x:
                                min_price_greater_than_x = min([(value, y_values[x_values.index(value)]) for value in
                                                                x_values_greater_than_x], key=lambda val: val[1],
                                                               default=None)

                                if min_price_greater_than_x is not None:
                                    x_min_price_greater_than_x, price_min_price_greater_than_x\
                                        = min_price_greater_than_x
                                    print("Minimum price greater than x in the density range:")
                                    print("Size:", x_min_price_greater_than_x)
                                    print("Cost:", price_min_price_greater_than_x)

                                    # 对比价格
                                    if optimal_result is not None:
                                        closest_x = optimal_result["Closest X in Range"]
                                        closest_x_price = optimal_result["Closest X Price in Range"]
                                        if price_min_price_greater_than_x is not None:
                                            if closest_x_price is not None:
                                                if price_min_price_greater_than_x < closest_x_price:
                                                    optimal_size = x_min_price_greater_than_x
                                                    optimal_cost = price_min_price_greater_than_x
                                                else:
                                                    optimal_size = closest_x
                                                    optimal_cost = closest_x_price
                                            else:
                                                optimal_size = x_min_price_greater_than_x
                                                optimal_cost = price_min_price_greater_than_x
                                        else:
                                            if closest_x_price is not None:
                                                optimal_size = closest_x
                                                optimal_cost = closest_x_price
                                            else:
                                                optimal_size = None
                                                optimal_cost = None

                                    else:
                                        optimal_size = x_min_price_greater_than_x
                                        optimal_cost = price_min_price_greater_than_x

                                    component_results.append([project_name, comp_name, x_target, optimal_size,
                                                              optimal_cost])

                else:
                    print("The threshold is not on the Gaussian KDE curve.")

                    # 计算原始数据的 size 值的标准差
                    range_max = x_values_extra[0]
                    x_values_in_non_density_range = [value for value in x_values if value < range_max]
                    x_std = np.std(x_values_in_non_density_range)
                    print("Standard deviation of x values in the high-density range:", x_std)

                    # 在原始数据中找到所有密度在range_max之前的 x 值
                    x_values_less_than_x = [value for value in x_values if (kde(range_max) <= kde(value)
                                                                            <= kde(x_max_density)
                                                                            and (x_target - x_std)
                                                                            <= value <= (x_target + x_std))]
                    print("X values less than x in the density range are:", x_values_less_than_x)

                    x_values_greater_than_x = [value for value in x_values if value >= x_target]
                    print("X values greater than x in the density range are:", x_values_greater_than_x)

                    # 定义误差范围值
                    error_range_values = [0.0025, 0.005, 0.0075, 0.01]

                    # 存储结果的列表
                    sensitivity_results = []

                    # 遍历不同的误差范围值
                    for error_range in error_range_values:
                        # 计算误差范围
                        x_error_range = x_std * error_range

                        # 找到在误差范围内与 x 最接近的数值
                        closest_x_in_range = [val for val in x_values_less_than_x if abs(val - x_target)
                                              <= x_error_range]
                        closest_x_price_in_range = [y_values[x_values.index(val)] for val in closest_x_in_range]

                        # 确保找到的值在误差范围内
                        if all(abs(x - x_target) <= x_error_range for x in closest_x_in_range):
                            min_cost_in_range = min(zip(closest_x_in_range, closest_x_price_in_range),
                                                    key=lambda val: val[1], default=None)
                            if min_cost_in_range is not None:
                                closest_x, closest_x_price = min_cost_in_range
                                print("Closest x value within the error range:", closest_x)
                                print("Corresponding price less than x in the density range within the error range:")
                                print("Size:", closest_x)
                                print("Cost:", closest_x_price)
                            else:
                                closest_x = None
                                closest_x_price = None
                                print("No corresponding price found for the closest x value within the error range.")
                        else:
                            closest_x = None
                            closest_x_price = None
                            print("No values within the error range.")

                        # 存储敏感度分析结果
                        sensitivity_results.append({"Error Range": error_range,
                                                    "Closest X in Range": closest_x,
                                                    "Closest X Price in Range": closest_x_price})

                    # 比较结果并选择具有最小cost的error_range_values
                    optimal_result = None
                    min_cost = float('inf')  # 初始化最小cost为正无穷大
                    for result in sensitivity_results:
                        closest_x_price = result["Closest X Price in Range"]
                        if closest_x_price is not None and closest_x_price < min_cost:
                            min_cost = closest_x_price
                            optimal_result = result

                    # 打印最佳结果
                    if optimal_result is not None:
                        print("Optimal Result:")
                        print("Error Range:", optimal_result["Error Range"])
                        print("Closest X in Range:", optimal_result["Closest X in Range"])
                        print("Closest X Price in Range:", optimal_result["Closest X Price in Range"])
                    else:
                        print("No optimal result found.")

                    # 确保找到的值在误差范围内
                    if optimal_result is not None:
                        optimal_size = optimal_result["Closest X in Range"]
                        optimal_cost = optimal_result["Closest X Price in Range"]
                    else:
                        optimal_size = None
                        optimal_cost = None

                    # 找到比 x 大的价格最低的数值
                    if x_values_greater_than_x:
                        min_price_greater_than_x = min([(value, y_values[x_values.index(value)]) for value in
                                                        x_values_greater_than_x], key=lambda val: val[1],
                                                       default=None)

                        if min_price_greater_than_x is not None:
                            x_min_price_greater_than_x, price_min_price_greater_than_x = min_price_greater_than_x
                            print("Minimum price greater than x in the density range:")
                            print("Size:", x_min_price_greater_than_x)
                            print("Cost:", price_min_price_greater_than_x)

                            # 对比价格
                            if optimal_result is not None:
                                closest_x = optimal_result["Closest X in Range"]
                                closest_x_price = optimal_result["Closest X Price in Range"]
                                if price_min_price_greater_than_x is not None:
                                    if closest_x_price is not None:
                                        if price_min_price_greater_than_x < closest_x_price:
                                            optimal_size = x_min_price_greater_than_x
                                            optimal_cost = price_min_price_greater_than_x
                                        else:
                                            optimal_size = closest_x
                                            optimal_cost = closest_x_price
                                    else:
                                        optimal_size = x_min_price_greater_than_x
                                        optimal_cost = price_min_price_greater_than_x
                                else:
                                    if closest_x_price is not None:
                                        optimal_size = closest_x
                                        optimal_cost = closest_x_price
                                    else:
                                        optimal_size = None
                                        optimal_cost = None

                            else:
                                optimal_size = x_min_price_greater_than_x
                                optimal_cost = price_min_price_greater_than_x

                            component_results.append([project_name, comp_name, x_target, optimal_size,
                                                      optimal_cost])

                # 结束计时
                end_time = time.time()

                # 计算并打印运行时间
                elapsed_time = end_time - start_time
                print("The code ran in", elapsed_time, "seconds.")

                # 确定保存路径
                output_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                             'data', 'opt_output', 'times_taken')

                # 确保目标文件夹存在
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                # 文件路径
                filename = os.path.join(output_folder, 'optimized_times_dpm_2.csv')

                # 检查文件是否存在，如果不存在或者为空，写入标题行
                if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                    with open(filename, 'w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(['Project_Name', 'Elapsed_Time', None])

                # 将项目名和时间记录到CSV文件中
                with open(filename, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([f'{j}_project_{i}_{comp_name}_dpm_2', elapsed_time])

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
                print(f"File path for {comp_name} - {model}: {file_path}")

                # 读取CSV文件并提取"data-pair"列的数据
                df_comp = pd.read_csv(file_path)

                # 检查是否存在"data-pair"列
                if "data-pair" not in df_comp.columns:
                    print(f"Skipping {comp_name} - {model} due to missing 'data-pair' column.")
                    data_strings.append(comp_name)
                    continue

            else:
                print(f"No matching file found for {comp_name} - {model}")
                data_strings.append(comp_name)

        # 将没有"data-pair"的组件保存到DataFrame中
        df_output['component'] = data_strings
        print(data_strings)

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
                                       'opt_output', 'output_dpm_2')
        os.makedirs(output_folder_1, exist_ok=True)

        output_file_path = os.path.join(output_folder_1, f'{j}_component_optimal_data_{i}.csv')
        write_to_csv(component_results, output_file_path)

        # 读取CSV文件的所有数据
        df = pd.read_csv(output_file_path)

        # 按照 'comp_name' 和 'project_name' 排序
        df_sorted = df.sort_values(by=['comp_name', 'project_name'])

        # 保存排序后的数据到CSV文件
        output_folder_2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_2_sorted')
        os.makedirs(output_folder_2, exist_ok=True)

        # 将排序后的数据保存到新的CSV文件
        sorted_output_file_path = os.path.join(output_folder_2, f'{j}_sorted_component_optimal_data_{i}.csv')
        df_sorted.to_csv(sorted_output_file_path, index=False)

        print('===================================================================================================')

        # 读取原始数据文件
        output_folder_2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_2_sorted')
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
                                       'opt_output', 'output_dpm_2_matched')
        os.makedirs(output_folder_3, exist_ok=True)

        # 将更新后的 df DataFrame 保存到新的 CSV 文件
        matched_output_file_path = os.path.join(output_folder_3, f'{j}_matched_component_optimal_data_{i}.csv')
        df.to_csv(matched_output_file_path, index=False)

        print('================================================================================================')

        base_directory = os.path.dirname(os.path.abspath(__file__))
        basic_file_path = os.path.join(base_directory, '..', 'data', 'topology', 'basic_neu', f'basic_{i}.csv')
        output_file_path = os.path.join(base_directory, '..', 'data', 'opt_output', 'output_dpm_2_sorted',
                                        f'{j}_sorted_component_optimal_data_{i}.csv')

        df_optimal = pd.read_csv(output_file_path)
        df_basic = pd.read_csv(basic_file_path)

        new_directory = os.path.join(base_directory, '..', 'data', 'topology', 'basic_modi_dpm_2')
        os.makedirs(new_directory, exist_ok=True)

        df_basic_list = [df_basic.copy() for _ in range(len(project_names))]
        new_basic_file_paths = [f'{j}_basic_project_{i}_{j_2}_dpm_2.csv' for j_2 in range(len(project_names))]

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
