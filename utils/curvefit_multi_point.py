# Description: Curve fitting for multiple points
import os
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt

# Read the data points from the file
def extract_data_points(file_path):
    # Reading the CSV file
    df = pd.read_csv(file_path)

    # Extracting the 'data-pair' column
    data_pair_column = df['data-pair'].dropna()

    # Extracting the data points
    data_points = []
    for entry in data_pair_column:
        points = [tuple(map(float, point.split(';'))) for point in
                  entry.split('/')]
        data_points.extend(points)

    return data_points


def find_combinations(current_combination, remaining_kw, devices, max_repeat,
                      max_combination_length):
    '''Recursive function to find all possible combinations of devices to fulfill the required kW.'''

    # If the remaining kW is less than or equal to 0 or if the current combination reaches the max length
    # Return the current combination (if kW requirement is met) or an empty list
    if remaining_kw <= 0 or len(current_combination) == max_combination_length:
        return [current_combination] if remaining_kw >= 0 else []

    combinations = []

    # Always include the current combination if its length is between 1 and max_combination_length
    if 0 < len(current_combination) <= max_combination_length:
        combinations.append(current_combination)

    for device in devices:
        if current_combination.count(device) < max_repeat:
            next_combination = current_combination + [device]
            next_remaining_kw = remaining_kw - device[0]
            combinations.extend(
                find_combinations(next_combination, next_remaining_kw, devices,
                                  max_repeat, max_combination_length))

    return combinations

# Curve fitting for multiple points
def curvefit_multi_point(data_path):
    # Extracting the data points
    points = extract_data_points(data_path)

    # find all possible combinations of devices to fulfill the required kW
    max_repeat = 3
    max_combination_length = 3 # todo: change for different devices
    remaining_kw = 20000  # todo: change for different devices
    combinations = find_combinations([], remaining_kw, points, max_repeat,
                             max_combination_length)

    # 1. Calculate the total kW and price for each combination
    total_kws = [sum([device[0] for device in combination]) for combination in
                 combinations]
    total_prices = [sum([device[1] for device in combination]) for
                    combination in combinations]
    #
    # # 2. Linear regression fit using the total kW and price
    # fit_model = LinearRegression()
    # fit_model.fit(np.array(total_kws).reshape(-1, 1), total_prices)
    # # Extracting slope and intercept from the fit model
    # slope = fit_model.coef_[0]
    # intercept = fit_model.intercept_
    #
    # # Constructing the equation string
    # equation_str = "y = {:.2f}x + {:.2f}".format(slope, intercept)
    # predicted_prices = fit_model.predict(np.array(total_kws).reshape(-1, 1))
    #
    # # 3. Visualization
    # plt.figure(figsize=(10, 6))
    # plt.scatter(total_kws, total_prices, color='blue', marker='o',
    #             label='Combinations Data Points')
    # plt.plot(total_kws, predicted_prices, color='red', label='Fit Line')
    # plt.title('Linear Fit for Device Combinations')
    # plt.xlabel('Total kW of Combination')
    # plt.ylabel('Total Price of Combination')
    # plt.text(0.75 * max(total_kws), 0.85 * max(total_prices), equation_str,
    #          fontsize=12, color='red',
    #          bbox=dict(facecolor='white', edgecolor='red'))
    # plt.legend(loc='upper left')
    # plt.grid(True)
    # plt.show()
    cheapest_combinations = {}

    for kw, price, combination in zip(total_kws, total_prices, combinations):
        if kw not in cheapest_combinations:
            cheapest_combinations[kw] = {'price': price,
                                         'combination': combination}
        else:
            # If the current combination is cheaper than the previously stored one, update the entry
            if price < cheapest_combinations[kw]['price']:
                cheapest_combinations[kw] = {'price': price,
                                             'combination': combination}

    # Extracting the cheapest combinations and their respective prices and total kWs
    cheapest_total_kws = list(cheapest_combinations.keys())
    cheapest_total_prices = [entry['price'] for entry in
                             cheapest_combinations.values()]

    # 2. Linear regression fit using the total kW and price of the cheapest combinations
    fit_model = LinearRegression()
    fit_model.fit(np.array(cheapest_total_kws).reshape(-1, 1),
                  cheapest_total_prices)
    predicted_prices = fit_model.predict(
        np.array(cheapest_total_kws).reshape(-1, 1))

    # Extracting slope and intercept from the fit model
    slope = fit_model.coef_[0]
    intercept = fit_model.intercept_

    # Constructing the equation string
    equation_str = "y = {:.2f}x + {:.2f}".format(slope, intercept)

    # 3. Visualization
    plt.figure(figsize=(10, 6))
    plt.scatter(cheapest_total_kws, cheapest_total_prices, color='blue',
                marker='o', label='Cheapest Combinations Data Points')
    plt.plot(cheapest_total_kws, predicted_prices, color='red',
             label='Fit Line')
    plt.title('Linear Fit for Cheapest Device Combinations')
    plt.xlabel('Total kW of Combination')
    plt.ylabel('Total Price of Combination')

    # Adjusting the text position to upper right corner
    plt.text(0.75 * max(cheapest_total_kws), 0.85 * max(cheapest_total_prices),
             equation_str, fontsize=12, color='red',
             bbox=dict(facecolor='white', edgecolor='red'))

    # Adjusting the legend's position
    plt.legend(loc='upper left')

    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    data_path = os.path.join('..', 'data', 'component_database', 'HotWaterStorage',
                             'all_brands-Storage_technology-buffer_storage-0_Heat_exchanger.csv')
    # data_path = os.path.join('..', 'data', 'component_database', 'HeatPump',
    #                          'all_brands-Heat_pumps-air-water.csv')
    curvefit_multi_point(data_path)
