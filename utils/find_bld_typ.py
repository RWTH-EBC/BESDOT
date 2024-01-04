import os
import pandas as pd


def find_city_bld_typ(target_city):
    current_directory = os.path.dirname(os.path.abspath(__file__))

    csv_file_path = os.path.join(current_directory, "../data/subsidy/city_subsidy.csv")

    if os.path.exists(csv_file_path):
        data = pd.read_csv(csv_file_path)

        city_data = data[data['City'] == target_city]
        building_types_data = city_data['Building Type'].unique()

        return building_types_data

    else:
        return None


def find_state_bld_typ(target_state):
    current_directory = os.path.dirname(os.path.abspath(__file__))

    csv_file_path = os.path.join(current_directory, "../data/subsidy/state_subsidy.csv")

    if os.path.exists(csv_file_path):
        data = pd.read_csv(csv_file_path)

        city_data = data[data['State'] == target_state]
        building_types_data = city_data['Building Type'].unique()

        return building_types_data

    else:
        return None


def find_country_bld_typ(target_country):
    current_directory = os.path.dirname(os.path.abspath(__file__))

    csv_file_path = os.path.join(current_directory, "../data/subsidy/country_subsidy_BAFA.csv")

    if os.path.exists(csv_file_path):
        data = pd.read_csv(csv_file_path)

        city_data = data[data['Country'] == target_country]
        building_types_data = city_data['Building Type'].unique()

        return building_types_data

    else:
        return None


"""
city = "Stuttgart"
building_types_city = find_city_bld_typ(city)

if building_types_city is not None:
    print(f"Building Types for {city}: {building_types_city}")
else:
    print(f"City {city} data not found.")

state = "Baden-Wuerttemberg"
building_types_state = find_state_bld_typ(state)

if building_types_state is not None:
    print(f"Building Types for {state}: {building_types_state}")
else:
    print(f"State {state} data not found.")

country = "Germany"
building_types_country = find_country_bld_typ(country)

if building_types_country is not None:
    print(f"Building Types for {country}: {building_types_country}")
else:
    print(f"Country {country} data not found.")
"""
