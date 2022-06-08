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

# ==============================================================================
#                       Path for inputs and outputs
# ==============================================================================

# Automatic Data Imports
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_profile_path = os.path.join(base_path, "data", "tek_data",
                                  "DHW_profile.xlsx")
output_path = os.path.join(base_path, "data", "tek_data",
                           "output_hot_water_profile")


def gen_hot_water_profile(building_typ,
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
    hot_water_heating_demand_array = np.array(
        hot_water_heating_demand_df[
        'Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'])
    hot_water_heating_demand_list = hot_water_heating_demand_array.tolist()
    return hot_water_heating_demand_list



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
    profile_df = pd.read_excel(input_profile_path, sheet_name='DIN V 18599')
    # print(zone)
    # print(profile_df.loc[profile_df['Raumtyp'] == zone])
    start_time = profile_df.loc[profile_df['Raumtyp'] == zone][
        'Nutzungszeit_von'].values[0]
    end_time = profile_df.loc[profile_df['Raumtyp'] == zone][
        'Nutzungzeit_bis'].values[0]
    if end_time == 0:
        end_time = 24  # 24:00 is 0:00

    status_list = []
    if profile_df.loc[profile_df['Raumtyp'] == zone]['Nutzungstage'].values[
        0] in [150, 200, 230, 250]:
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


