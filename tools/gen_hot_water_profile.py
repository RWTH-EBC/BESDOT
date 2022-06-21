"""
This tool use the TEK project of IWU to calculate the annual energy demand of
the building and use the degree day method to generate the demand profile.
"""
import datetime
import os
from warnings import warn
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tools.gen_heat_profile import calc_bld_demand
from functools import reduce

# ==============================================================================
#                       Path for inputs and outputs
# ==============================================================================

# Automatic Data Imports
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_profile_path = os.path.join(base_path, "data", "tek_data",
                                  "DHW_profile.xlsx")
input_profile_path_GHD = os.path.join(base_path, "data", "tek_data",
                                      "GHD_profile.xlsx")
output_path = os.path.join(base_path, "data", "tek_data",
                           "output_hot_water_profile")
input_zone_path = os.path.join(base_path, "data", "tek_data",
                               "GHD_Zonierung.xlsx")


def gen_hot_water_profile(building_typ, area, year=2021, energy_typ="mittel"):
    new_zone_df = analysis_bld_zone(building_typ, area)
    for row in range(len(new_zone_df)):
        zone = new_zone_df.loc[row, 'DIN_Zone']

    bld_hot_water_demand = calc_bld_demand(building_typ, area, 'hot_water', energy_typ)
    hot_water_heating_demand_df = pd.read_excel(input_profile_path, sheet_name='DHW', header=None, usecols=[1],
                                                skiprows=1)
    hot_water_heating_demand_df.columns = ['Wärmebedarf für Trinkwassererwärmung (kWh)']
    hot_water_heating_demand_df['Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'] = \
        hot_water_heating_demand_df['Wärmebedarf für Trinkwassererwärmung (kWh)'].map(
            lambda x: x / (4180 * 300 * (60 - 12) / 3600 / 1000 * 365) * bld_hot_water_demand)
    hot_water_heating_demand_array = np.array(
        hot_water_heating_demand_df['Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'])
    hot_water_heating_demand_list = hot_water_heating_demand_array.tolist()

    if building_typ != 'Wohngebäude':
        hour_status_array = np.array(op_time_status(year, zone))
        hour_status_list = op_time_status(year, zone)
        total_hot_water_profile_array = np.multiply(hour_status_array, hot_water_heating_demand_array)

    return total_hot_water_profile_array


def op_time_status(year, zone):
    """
    Calculate the operating time for whole year. The weekend and work time
    could be considered in this function. For different thermal zone the
    operating time also varies according to DIN V 18599.
    Args:
        year: int, target year
        zone: str, the name should be same as in the standard DIN V 18599
    Returns:
        List of status for each hour in whole year
    """
    weekday_list = find_weekday(year)
    profile_df = pd.read_excel(input_profile_path_GHD, sheet_name='DIN V 18599')
    # print(zone)
    # print(profile_df.loc[profile_df['Raumtyp'] == zone])
    start_time = 7
    end_time = 18
    if end_time == 0:
        end_time = 24  # 24:00 is 0:00

    status_list = []
    if profile_df.loc[profile_df['Raumtyp'] == zone]['Nutzungstage'].values[0] in [150, 200, 230, 250]:
        # The zone are only used in weekday. Zone such as audience hall
        # with 150 operating days and Zone auch as fabric with 230 operating
        # days are also considered as the other working zone.
        day = 0
        while day < 365:
            day_status = [0] * 24
            if weekday_list[day] in [0, 1, 2, 3, 4]:
                day_status[start_time:end_time] = [1] * (end_time - start_time)
            status_list += day_status
            day += 1
    elif profile_df.loc[profile_df['Raumtyp'] == zone]['Nutzungstage'].values[
        0] == 300:
        # The zone which are only used in weekday and Saturday, like restaurant
        day = 0
        while day < 365:
            day_status = [0] * 24
            if weekday_list[day] in [0, 1, 2, 3, 4, 5]:
                day_status[start_time:end_time] = [1] * (end_time - start_time)
            status_list += day_status
            day += 1
    elif profile_df.loc[profile_df['Raumtyp'] == zone]['Nutzungstage'].values[
        0] == 365:
        # The zone are used everyday, such as bedroom
        day = 0
        while day < 365:
            day_status = [0] * 24
            day_status[start_time:end_time] = [1] * (end_time - start_time)
            status_list += day_status
            day += 1
    else:
        # The zone such as hall are not considered
        warn('The operating days of zone' + zone + 'does not match the DIN V '
                                                   '18599')

    return status_list


def find_weekday(year):
    """
    Create a list of weekdays throughout the year. The holidays are not
    considered in the function.
    Leap years are also considered to have only 365 days to reduce the work.
    Args:
        year: int, target year
    Returns:
        list, status for whole year
    """
    # weekday() == 4 means Friday, the value could be from 0 to 6
    day = datetime.date(year, 1, 1).weekday()
    weekday_list = []

    i = 0
    while i < 365:
        weekday_list.append(day)
        day = (day + 1) % 7
        i += 1

    return weekday_list


def gen_hot_water_profile_1(building_typ,
                            area,
                            energy_typ="mittel",
                            plot=False,
                            save_plot=False):
    bld_hot_water_demand = calc_bld_demand(building_typ, area, 'hot_water',
                                           energy_typ)
    hot_water_heating_demand_df = pd.read_excel(input_profile_path,
                                                sheet_name='DHW',
                                                header=None, usecols=[2],
                                                skiprows=1)
    hot_water_heating_demand_df.columns = [
        'Wärmebedarf für Trinkwassererwärmung (kWh)']
    hot_water_heating_demand_df[
        'Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'] = \
        hot_water_heating_demand_df[
            'Wärmebedarf für Trinkwassererwärmung (kWh)'].map(
            lambda x: x / (4180 * 300 * (
                    60 - 12) / 3600 / 1000 * 365) * bld_hot_water_demand)
    if building_typ != 'Wohngebäude':

        for m in range(1, 53):  # 53weeks
            for n in range(7 * 24 * (m - 1) + 5 * 24, 7 * 24 * (m - 1) + 7 * 24 + 1):
                hot_water_heating_demand_df[
                    'Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'].iloc[n] = 0

        for x in range(1, 366):
            for y in range(24 * (x - 1), 7 + 24 * (x - 1)):
                hot_water_heating_demand_df[
                    'Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'].iloc[y] = 0
            for y in range(19 + 24 * (x - 1), 24 * x):
                hot_water_heating_demand_df[
                    'Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'].iloc[y] = 0

    hot_water_heating_demand_array = np.array(
        hot_water_heating_demand_df[
            'Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'])
    hot_water_heating_demand_list = hot_water_heating_demand_array.tolist()

    plt.figure()
    plt.plot(hot_water_heating_demand_list)
    plt.ylabel('Hot Water Profile')
    plt.xlabel('Hours [h]')
    plt.ylim(ymin=0)
    plt.xlim(xmin=0)
    plt.grid()
    plt.savefig(os.path.join(base_path, "data", "tek_data", 'hot_water_profile_figure.jpg'))
    plt.show()

    return hot_water_heating_demand_list


def analysis_bld_zone(building_typ, area):
    """Analysis the thermal zones in building, the zone, which is smaller
    than the min_zone_area should be ignored. The min_zone_area is hard coded
    with 2 m², which could be fixed later or not :)"""
    zone_df = pd.read_excel(input_zone_path, sheet_name=building_typ,
                            header=None, usecols=range(5), skiprows=2)
    zone_df.columns = ['Nr', 'Zone', 'Percentage', 'kum_per', 'DIN_Zone']
    # 1st try to calculate the area of each zone
    zone_df['Area'] = zone_df['Percentage'].map(lambda x: x * area)

    # Too small zones should be delete
    min_zone_area = 2
    new_zone_df = zone_df[zone_df['Area'] > min_zone_area]

    # Recalculate percentage
    sum_per = new_zone_df['Percentage'].sum()
    pd.options.mode.chained_assignment = None
    new_zone_df['new_per'] = new_zone_df['Percentage'].map(
        lambda x: x / sum_per)
    new_zone_df['new_area'] = new_zone_df['Area'].map(lambda x: x / sum_per)

    return new_zone_df
