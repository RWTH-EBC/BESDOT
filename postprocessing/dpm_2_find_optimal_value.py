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

        base_directory = os.path.dirname(os.path.abspath(__file__))
        topology_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'topology', 'basic_neu')
        component_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'component_database')

        basic_file = os.path.join(topology_folder, f'basic_{i}.csv')
        df_basic = pd.read_csv(basic_file)

        data_strings = []

        for _, row in df_basic.iterrows():
            comp_type = row['comp_type']
            comp_name = row['comp_name']
            model = row['model']

            comp_folder = os.path.join(component_folder, comp_type)
            matching_files = [file for file in os.listdir(comp_folder) if file.startswith(model)]

            if len(matching_files) > 0:
                file_path = os.path.join(comp_folder, matching_files[0])

                df_comp = pd.read_csv(file_path)

                if "data-pair" not in df_comp.columns:
                    continue

                data_str = df_comp["data-pair"].values[0]
                data_strings.append((comp_name, data_str))

            else:
                print(f"No matching file found for {comp_name} - {model}")

        for i_1, (comp_name, data_str) in enumerate(data_strings):
            print(data_str)

            pairs_str = data_str.split("/")

            x_values = []
            y_values = []

            for pair_str in pairs_str:
                size_str, cost_str = pair_str.split(";")
                x_values.append(float(size_str))
                y_values.append(float(cost_str))

            x_values, y_values = zip(*sorted(zip(x_values, y_values), key=lambda pair: pair[1]))

            sorted_data_str = "/".join(["{:.1f};{:.1f}".format(x, y) for x, y in zip(x_values, y_values)])

            print("Sorted data string:")
            print(sorted_data_str)

            kde = gaussian_kde(x_values)

            x_plot = np.linspace(min(x_values), max(x_values), 500)

            density = kde(x_plot)

            mu, std = norm.fit(x_values)

            threshold = mu - std
            threshold_density = kde(threshold)

            plt.grid()
            plt.plot(x_plot, density)

            y_intersection = kde(threshold)

            if y_intersection <= 0:
                print("No intersection between the threshold line and the KDE curve.")

            plt.axhline(y=y_intersection, color='g', linestyle='--', label='Additional Line')

            extra_intersection = x_plot[np.argwhere(np.diff(np.sign(density - y_intersection)) != 0).flatten()]

            x_values_extra = []

            for intersection in extra_intersection:
                plt.axvline(x=intersection, color='g', linestyle='--', label='Additional Line')
                x_values_extra.append(intersection)

            print("X values of the additional lines are:", x_values_extra)

            if len(x_values_extra) == 1:
                print("Insufficient additional intersection points found.")
                range_min = x_values[0]  # 将range_min设置为原始数据的第一个值
                range_max = x_values_extra[0]
                print("High-density range:", range_min, "-", range_max)
            else:
                x_values_extra.sort()

                range_min = x_values_extra[0]
                range_max = x_values_extra[1]

                print("High-density range:", range_min, "-", range_max)

            max_density = max(density)
            max_density_index = np.argmax(density)
            x_max_density = x_plot[max_density_index]

            print("Maximum density is", max_density)
            print("X value corresponding to the maximum density is", x_max_density)

            save_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'diagram_density_plot_component')

            os.makedirs(save_folder, exist_ok=True)

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

                start_time = time.time()

                if min(x_values) < threshold < max(x_values):
                    print("The threshold is on the Gaussian KDE curve.")

                    threshold_density = kde(threshold)

                    range_min = x_values_extra[0]
                    range_max = x_values_extra[1]

                    if range_min <= x_target <= range_max:
                        print("The threshold is in the high-density range.")

                        x_values_in_high_density_range = [value for value in x_values if range_min < value < range_max]

                        x_std = np.std(x_values_in_high_density_range)
                        print("Standard deviation of x values in the high-density range:", x_std)

                        x_values_less_than_x = [value for value in x_values if (max_density >= kde(value)
                                                                                >= threshold_density)
                                                and (x_target - x_std) <= value <= (x_target + x_std)]
                        print("X values less than x in the density range are:", x_values_less_than_x)

                        x_values_greater_than_x = [value for value in x_values if value >= x_target]
                        print("X values greater than x in the density range are:", x_values_greater_than_x)

                        # Define the error range value
                        error_range_values = [0.04, 0.06, 0.08, 0.10]

                        sensitivity_results = []

                        for error_range in error_range_values:
                            x_error_range = x_std * error_range

                            closest_x_in_range = [val for val in x_values_less_than_x if abs(val - x_target)
                                                  <= x_error_range]
                            closest_x_price_in_range = [y_values[x_values.index(val)] for val in closest_x_in_range]

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

                            sensitivity_results.append({"Error Range": error_range,
                                                        "Closest X in Range": closest_x,
                                                        "Closest X Price in Range": closest_x_price})

                        optimal_result = None
                        min_cost = float('inf')
                        for result in sensitivity_results:
                            closest_x_price = result["Closest X Price in Range"]
                            if closest_x_price is not None and closest_x_price < min_cost:
                                min_cost = closest_x_price
                                optimal_result = result

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

                        if optimal_result is not None:
                            optimal_size = optimal_result["Closest X in Range"]
                            optimal_cost = optimal_result["Closest X Price in Range"]
                        else:
                            optimal_size = None
                            optimal_cost = None

                        if x_values_greater_than_x:
                            min_price_greater_than_x = min([(value, y_values[x_values.index(value)]) for value in
                                                            x_values_greater_than_x], key=lambda val: val[1],
                                                           default=None)

                            if min_price_greater_than_x is not None:
                                x_min_price_greater_than_x, price_min_price_greater_than_x = min_price_greater_than_x
                                print("Minimum price greater than x in the density range:")
                                print("Size:", x_min_price_greater_than_x)
                                print("Cost:", price_min_price_greater_than_x)

                                # price comparison
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
                        print("The threshold is in the low-density range.")

                        if x_target < range_min:
                            x_values_in_low_density_range_1 = [value for value in x_values if value < range_min]

                            x_std = np.std(x_values_in_low_density_range_1)
                            print("Standard deviation of x values in the high-density range:", x_std)

                            x_values_less_than_x = [value for value in x_values if (kde(value) <= kde(range_min)
                                                                                    and (x_target - x_std)
                                                                                    <= value <= (x_target + x_std))]
                            print("X values less than x in the density range are:", x_values_less_than_x)

                            x_values_greater_than_x = [value for value in x_values if value >= x_target]
                            print("X values greater than x in the density range are:", x_values_greater_than_x)

                            error_range_values = [0.10, 0.15, 0.20, 0.25, 0.30]

                            sensitivity_results = []

                            for error_range in error_range_values:
                                x_error_range = x_std * error_range

                                min_x_error_range = np.amin(x_error_range)
                                max_x_error_range = np.amax(x_error_range)

                                closest_x_in_range = []
                                for val in x_values_less_than_x:
                                    if abs(val - x_target) >= min_x_error_range:
                                        closest_x_in_range.append(min_x_error_range <= abs(val - x_target))
                                    else:
                                        closest_x_in_range.append(abs(val - x_target) <= max_x_error_range)

                                closest_x_price_in_range = [y_values[i] for i, val in enumerate(x_values_less_than_x)
                                                            if closest_x_in_range[i]]

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

                                sensitivity_results.append({"Closest X in Range": closest_x,
                                                            "Closest X Price in Range": closest_x_price})

                            optimal_result = None
                            min_cost = float('inf')
                            for result in sensitivity_results:
                                closest_x_price = result["Closest X Price in Range"]
                                if closest_x_price is not None and closest_x_price < min_cost:
                                    min_cost = closest_x_price
                                    optimal_result = result

                            if optimal_result is not None:
                                print("Optimal Result:")
                                print("Closest X in Range:", optimal_result["Closest X in Range"])
                                print("Closest X Price in Range:", optimal_result["Closest X Price in Range"])
                            else:
                                print("No optimal result found.")

                            if optimal_result is not None:
                                optimal_size = optimal_result["Closest X in Range"]
                                optimal_cost = optimal_result["Closest X Price in Range"]
                            else:
                                optimal_size = None
                                optimal_cost = None

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

                        elif x_target > range_max:
                            x_values_in_low_density_range_2 = [value for value in x_values if value > range_max]

                            x_std = np.std(x_values_in_low_density_range_2)
                            print("Standard deviation of x values in the high-density range:", x_std)

                            # 在原始数据中找到所有密度在range_max之前的 x 值
                            x_values_less_than_x = [value for value in x_values if (kde(value) <= kde(range_max)
                                                                                    and (x_target - x_std)
                                                                                    <= value <= x_target + x_std)]
                            print("X values less than x in the density range are:", x_values_less_than_x)

                            x_values_greater_than_x = [value for value in x_values if value >= x_target]
                            print("X values greater than x in the density range are:", x_values_greater_than_x)

                            error_range_values = [0.02, 0.03, 0.04, 0.05, 0.06]

                            sensitivity_results = []

                            for error_range in error_range_values:
                                x_error_range = x_std * error_range

                                closest_x_in_range = [val for val in x_values_less_than_x if abs(val - x_target)
                                                      <= x_error_range]
                                closest_x_price_in_range = [y_values[x_values.index(val)] for val in closest_x_in_range]

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

                                sensitivity_results.append({"Error Range": error_range,
                                                            "Closest X in Range": closest_x,
                                                            "Closest X Price in Range": closest_x_price})

                            optimal_result = None
                            min_cost = float('inf')
                            for result in sensitivity_results:
                                closest_x_price = result["Closest X Price in Range"]
                                if closest_x_price is not None and closest_x_price < min_cost:
                                    min_cost = closest_x_price
                                    optimal_result = result

                            if optimal_result is not None:
                                print("Optimal Result:")
                                print("Error Range:", optimal_result["Error Range"])
                                print("Closest X in Range:", optimal_result["Closest X in Range"])
                                print("Closest X Price in Range:", optimal_result["Closest X Price in Range"])
                            else:
                                print("No optimal result found.")

                            if optimal_result is not None:
                                optimal_size = optimal_result["Closest X in Range"]
                                optimal_cost = optimal_result["Closest X Price in Range"]
                            else:
                                optimal_size = None
                                optimal_cost = None

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

                    range_max = x_values_extra[0]
                    x_values_in_non_density_range = [value for value in x_values if value < range_max]
                    x_std = np.std(x_values_in_non_density_range)
                    print("Standard deviation of x values in the high-density range:", x_std)

                    x_values_less_than_x = [value for value in x_values if (kde(range_max) <= kde(value)
                                                                            <= kde(x_max_density)
                                                                            and (x_target - x_std)
                                                                            <= value <= (x_target + x_std))]
                    print("X values less than x in the density range are:", x_values_less_than_x)

                    x_values_greater_than_x = [value for value in x_values if value >= x_target]
                    print("X values greater than x in the density range are:", x_values_greater_than_x)

                    error_range_values = [0.0025, 0.005, 0.0075, 0.01]

                    sensitivity_results = []

                    for error_range in error_range_values:
                        x_error_range = x_std * error_range

                        closest_x_in_range = [val for val in x_values_less_than_x if abs(val - x_target)
                                              <= x_error_range]
                        closest_x_price_in_range = [y_values[x_values.index(val)] for val in closest_x_in_range]

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

                        sensitivity_results.append({"Error Range": error_range,
                                                    "Closest X in Range": closest_x,
                                                    "Closest X Price in Range": closest_x_price})

                    optimal_result = None
                    min_cost = float('inf')
                    for result in sensitivity_results:
                        closest_x_price = result["Closest X Price in Range"]
                        if closest_x_price is not None and closest_x_price < min_cost:
                            min_cost = closest_x_price
                            optimal_result = result

                    if optimal_result is not None:
                        print("Optimal Result:")
                        print("Error Range:", optimal_result["Error Range"])
                        print("Closest X in Range:", optimal_result["Closest X in Range"])
                        print("Closest X Price in Range:", optimal_result["Closest X Price in Range"])
                    else:
                        print("No optimal result found.")

                    if optimal_result is not None:
                        optimal_size = optimal_result["Closest X in Range"]
                        optimal_cost = optimal_result["Closest X Price in Range"]
                    else:
                        optimal_size = None
                        optimal_cost = None

                    if x_values_greater_than_x:
                        min_price_greater_than_x = min([(value, y_values[x_values.index(value)]) for value in
                                                        x_values_greater_than_x], key=lambda val: val[1],
                                                       default=None)

                        if min_price_greater_than_x is not None:
                            x_min_price_greater_than_x, price_min_price_greater_than_x = min_price_greater_than_x
                            print("Minimum price greater than x in the density range:")
                            print("Size:", x_min_price_greater_than_x)
                            print("Cost:", price_min_price_greater_than_x)

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

                end_time = time.time()

                elapsed_time = end_time - start_time
                print("The code ran in", elapsed_time, "seconds.")

                output_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                             'data', 'opt_output', 'times_taken')

                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                filename = os.path.join(output_folder, 'optimized_times_dpm_2.csv')

                if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                    with open(filename, 'w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(['Project_Name', 'Elapsed_Time', None])

                with open(filename, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([f'{j}_project_{i}_{comp_name}_dpm_2', elapsed_time])

        df_output = pd.DataFrame(columns=['component'])

        data_strings = []

        for _, row in df_basic.iterrows():
            comp_type = row['comp_type']
            comp_name = row['comp_name']
            model = row['model']

            comp_folder = os.path.join(component_folder, comp_type)
            matching_files = [file for file in os.listdir(comp_folder) if file.startswith(model)]

            if len(matching_files) > 0:
                file_path = os.path.join(comp_folder, matching_files[0])
                print(f"File path for {comp_name} - {model}: {file_path}")

                df_comp = pd.read_csv(file_path)

                if "data-pair" not in df_comp.columns:
                    print(f"Skipping {comp_name} - {model} due to missing 'data-pair' column.")
                    data_strings.append(comp_name)
                    continue

            else:
                print(f"No matching file found for {comp_name} - {model}")
                data_strings.append(comp_name)

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
        for _, row in df_basic.iterrows():
            comp_name = row['comp_name']
            component_list.append(comp_name)

        file_name = 'result.csv'
        base_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(base_directory, '..', 'data', 'opt_output', f'{j}_project', f'{j}_project_{i}_2')
        project_name = f'{j}_project_{i}_2'
        result_file_path = os.path.join(data_directory, file_name)
        df_result = pd.read_csv(result_file_path)

        for comp_name in component_list:
            size_og_row = df_result[df_result.iloc[:, 1] == f'size_{comp_name}[None]']
            size_op_row = df_result[df_result.iloc[:, 1] == f'size_{comp_name}[None]']
            invest_op_row = df_result[df_result.iloc[:, 1] == f'invest_{comp_name}[None]']

            water_heat_capacity = 4.18 * 10 ** 3  # J/kgK
            water_density = 1  # kg/L
            temp_difference = 60  # K
            unit_conversion = 3600 * 1000  # J/kWh
            slope_conversion = unit_conversion / (water_heat_capacity * temp_difference)

            if size_og_row.empty:
                size_og = "None"
            else:
                size_og = size_og_row.iloc[0, 2]
                if comp_name == "water_tes":
                    size_og = round(size_og * slope_conversion)

            if size_op_row.empty:
                size_op = "None"
            else:
                size_op = size_op_row.iloc[0, 2]
                if comp_name == "water_tes":
                    size_op = round(size_op * slope_conversion)

            if invest_op_row.empty:
                invest_op = "None"
            else:
                invest_op = invest_op_row.iloc[0, 2]
                if comp_name == "water_tes":
                    invest_op = invest_op

            component_results.append([f'{j}_project_{i}_2', comp_name, size_og, size_op, invest_op])

        output_folder_1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_2')
        os.makedirs(output_folder_1, exist_ok=True)

        output_file_path = os.path.join(output_folder_1, f'{j}_component_optimal_data_{i}.csv')
        write_to_csv(component_results, output_file_path)

        df = pd.read_csv(output_file_path)

        df_sorted = df.sort_values(by=['comp_name', 'project_name'])

        output_folder_2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_2_sorted')
        os.makedirs(output_folder_2, exist_ok=True)

        sorted_output_file_path = os.path.join(output_folder_2, f'{j}_sorted_component_optimal_data_{i}.csv')
        df_sorted.to_csv(sorted_output_file_path, index=False)

        print('===================================================================================================')

        output_folder_2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_2_sorted')
        input_file_path = os.path.join(output_folder_2, f'{j}_sorted_component_optimal_data_{i}.csv')
        df = pd.read_csv(input_file_path)

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
            csv_file_path = os.path.join(output_folder_2, '../..', 'products_table', component_files[comp_name])

            df_gas = pd.read_csv(csv_file_path)

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

        output_folder_3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data',
                                       'opt_output', 'output_dpm_2_matched')
        os.makedirs(output_folder_3, exist_ok=True)

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
