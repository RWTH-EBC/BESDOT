
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt

def find_combinations(current_combination, remaining_kw, devices, max_repeat, max_combination_length):
    if remaining_kw <= 0 or len(current_combination) >= max_combination_length:
        return [current_combination] if remaining_kw >= 0 else []
    
    combinations = []
    for device in devices:
        if current_combination.count(device) < max_repeat:
            next_combination = current_combination + [device]
            next_remaining_kw = remaining_kw - device[0]
            combinations.extend(find_combinations(next_combination, next_remaining_kw, devices, max_repeat, max_combination_length))
            
    return combinations

if __name__ == "__main__":
    # Reading the data
    df = pd.read_csv("all_brands-Heat_pumps-air-water.csv")
    data_pair_column = df['data-pair'].dropna().iloc[0]
    devices = [tuple(map(float, point.split(';'))) for point in data_pair_column.split('/')]

    # Finding combinations
    max_repeat = 3
    max_combination_length = 5
    combinations = find_combinations([], 50, devices, max_repeat, max_combination_length)
    combination_prices = [sum([device[1] for device in combination]) for combination in combinations]
    min_price_index = combination_prices.index(min(combination_prices))
    min_price_combination = combinations[min_price_index]
    combination_x_values = [device[0] for device in min_price_combination]
    combination_y_values = [device[1] for device in min_price_combination]

    # Original fit
    x_values = [device[0] for device in devices]
    y_values = [device[1] for device in devices]
    original_model = LinearRegression()
    original_model.fit(np.array(x_values).reshape(-1, 1), y_values)
    original_predicted_y = original_model.predict(np.array(x_values).reshape(-1, 1))

    # Combination fit
    combination_model = LinearRegression()
    combination_model.fit(np.array(combination_x_values).reshape(-1, 1), combination_y_values)
    combination_predicted_y = combination_model.predict(np.array(combination_x_values).reshape(-1, 1))

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.scatter(x_values, y_values, color='blue', marker='o', label='Original Data Points')
    plt.plot(x_values, original_predicted_y, color='red', label='Original Fit Line')
    plt.scatter(combination_x_values, combination_y_values, color='purple', marker='x', label='Combination Data Points')
    plt.plot(combination_x_values, combination_predicted_y, color='green', linestyle='--', label='Combination Fit Line')
    plt.title('Comparison of Fit Lines')
    plt.xlabel('Energy Device Size')
    plt.ylabel('Device Price')
    plt.legend()
    plt.grid(True)
    plt.show()

