"""
This tool use the TEK project of IWU to calculate the annual energy demand of
the building and use the degree day method to generate the demand profile.
"""

import os
import datetime
from warnings import warn
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
#                     Non-residential Building List
# ==============================================================================

building_typ_list = ["Verwaltungsgebäude",
                     "Büro und Dienstleistungsgebäude",
                     "Hochschule und Forschung",
                     "Gesundheitswesen",
                     "Bildungseinrichtungen",
                     "Kultureinrichtungen",
                     "Sporteinrichtungen",
                     "Beherbergen und Verpflegen",
                     "Gewerbliche und industrielle",
                     "Verkaufsstätten",
                     "Technikgebäude"]
energy_typ_list = ["sehr hoch", "hoch", "mittel", "gering", "sehr gering"]

# ==============================================================================
#                       Path for inputs and outputs
# ==============================================================================

# Automatic Data Imports
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_profile_path = os.path.join(base_path, "data", "tek_data",
                                  "GHD_profile.xlsx")
input_energy_path = os.path.join(base_path, "data", "tek_data",
                                 "TEK_Teilenergiekennwerte.xlsx")
input_zone_path = os.path.join(base_path, "data", "tek_data",
                               "GHD_Zonierung.xlsx")
input_tabula_path = os.path.join(base_path, "data", "tek_data",
                                 "TABULA_data.xlsx")
output_path = os.path.join(base_path, "data", "tek_data", "output_heat_profile")


def gen_heat_profile(building_typ,
                     area,
                     temperature_profile,
                     year=2021,
                     energy_typ="mittel",
                     plot=False,
                     save_plot=False):
    """
    total_degree_day: K*h
    annual_value: kW*h, jährlicher Gesamt Heizwärmebedarf
    Using degree day method to calculate the heat profil, the set temperature depending
    on room type and heating start at the temperature of 15 degree.
    :return:
    """
    # Analysis thermal zones in building
    new_zone_df = analysis_bld_zone(building_typ, area)

    # Calculate demand in each zone and degree day method
    demand_df = pd.read_excel(input_energy_path, sheet_name=energy_typ)
    profile_df = pd.read_excel(input_profile_path, sheet_name='DIN V 18599')
    total_heat_profile = []
    total_heat_demand = 0
    for row in range(len(new_zone_df)):
        zone = new_zone_df.loc[row, 'DIN_Zone']  # Zone name in DIN
        print(zone)
        hour_status = op_time_status(year, zone)
        zone_area = new_zone_df.loc[row, 'new_area']
        zone_heat_demand = calc_zone_demand(demand_df, 'heat', zone, zone_area)
        zone_heat_profile = degree_day(zone, zone_heat_demand, profile_df,
                                       temperature_profile, hour_status)
        print(zone_heat_profile[2535:2540])
        total_heat_profile = np.sum([total_heat_profile, zone_heat_profile],
                                    axis=0)
        total_heat_demand += zone_heat_demand
        print(total_heat_profile[2535:2540])

    if plot:
        plot_profile(total_heat_profile, save_plot)

    return total_heat_profile


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


def calc_bld_demand(building_typ, area, energy_sector, energy_typ='mittel'):
    """Calculate the total demand of the building by adding up the demand of
    all thermal zones.
    energy_sector: the energy carrier, could be 'heat', 'cool', 'hot_water',
    'elec', the name is defined in method calc_zone_demand.
    energy_typ: the building energy typ, which is define by project TEK and
    describe the building energy level. It could be the items in energy_typ_list
    """
    # Analysis thermal zones in building
    new_zone_df = analysis_bld_zone(building_typ, area)

    bld_demand = 0
    demand_df = pd.read_excel(input_energy_path, sheet_name=energy_typ)
    for row in range(len(new_zone_df)):
        zone = new_zone_df.loc[row, 'DIN_Zone']
        zone_area = new_zone_df.loc[row, 'new_area']
        zone_demand = calc_zone_demand(demand_df, energy_sector, zone,
                                       zone_area)
        bld_demand += zone_demand

    return bld_demand


def calc_zone_demand(demand_df, demand_typ, zone_typ, zone_area):
    """Calculate the annual total heat demand for each thermal zone"""
    total_demand = 0  # Unit kWh

    column_name = ''
    column_name_light = 'Beleuchtung'
    column_name_other = 'Arbeitshilfen'
    if demand_typ == 'heat':
        column_name = 'Heizung'
    elif demand_typ == 'cool':
        column_name = 'Kühlkälte'
    elif demand_typ == 'hot_water':
        column_name = 'Warmwasser'
    elif demand_typ == 'elec':
        pass
    else:
        warn('The demand typ is not allowed!')

    if demand_typ == 'elec':
        zone_demand = demand_df[demand_df['Standard-Nutzungseinheiten'] ==
                                zone_typ][column_name_light].values[0] + \
                      demand_df[demand_df['Standard-Nutzungseinheiten'] ==
                                zone_typ][column_name_other].values[0]
    else:
        zone_demand = demand_df[demand_df['Standard-Nutzungseinheiten'] ==
                                zone_typ][column_name].values[0]
    total_demand += zone_demand * zone_area

    return total_demand


def degree_day(zone_typ, annual_value, profile_df, temperature_profile,
               status_list, night_lower=False):
    heat_profile = []
    start_temp = 15  # The limit for heating on or off, could be the same as
    # set temperature? 15 comes from the german
    set_temp_heat = profile_df[profile_df['Raumtyp'] == zone_typ][
        'Raum-Solltemperatur_Heizung '].values[0]

    if night_lower:
        night_lower_temp(zone_typ, profile_df)
    else:
        total_degree_day = 0
        for time_step in range(8760):
            if temperature_profile[time_step] < start_temp and \
                    status_list[time_step] == 1:
                total_degree_day += (set_temp_heat - temperature_profile[
                    time_step])

        for time_step in range(8760):
            if temperature_profile[time_step] < start_temp and \
                    status_list[time_step] == 1:
                heat_profile.append(
                    (set_temp_heat - temperature_profile[time_step]) /
                    total_degree_day * annual_value)
            else:
                heat_profile.append(0)

    # print(heat_profile)
    return heat_profile


def night_lower_temp(zone_typ, profile_df):
    night = [22, 23, 24, 1, 2, 3, 4, 5, 6, 7]
    low = profile_df['Temperaturabsenkung']
    # todo: add this new function for night lower set temperature


def plot_profile(heat_profile, save_plot=False):
    plt.figure()
    plt.plot(heat_profile)
    plt.ylabel('Heat Profile')
    plt.xlabel('Hours [h]')
    plt.ylim(ymin=0)
    plt.xlim(xmin=0)
    plt.grid()
    if save_plot:
        plt.savefig(os.path.join(output_path, 'heat_profile_figure.jpg'))
    plt.show()


def calc_residential_demand(bld_type, bld_year, bld_area,
                            method='TABULA Berechnungsverfahren / korrigiert '
                                   'auf Niveau von Verbrauchswerten',
                            scenario='Ist-Zustand'):
    """According to the IWU TABULA calculate the space heating demand and hot
    water demand. The details of the method could be found in the project
    report 'DE_TABULA_TypologyBrochure_IWU.pdf'
    bld_type: building type, could be 'SFH', 'MFH', 'TH', 'AB'
    bld_year: building construction year, used to find the building class
    bld_area: area of the building
    """
    tabula_df = pd.read_excel(input_tabula_path)
    bld = tabula_df[(tabula_df['Gebäudetyp'] == bld_type) &
                    (tabula_df['Baualtersklasse_von'] < bld_year) &
                    (tabula_df['Baualtersklasse_bis'] >= bld_year) &
                    (tabula_df['Berechnungsverfahren'] == method) &
                    (tabula_df['Szenario'] == scenario)]

    heating_demand = bld['Heizung (Wärmeerzeugung)'].values[0] * bld_area
    hot_water_demand = bld['Warmwasser (Wärmeerzeugung)'].values[0] * bld_area

    print(heating_demand)
    print(hot_water_demand)
    return heating_demand, hot_water_demand


if __name__ == "__main__":
    input_temp_path = os.path.join(base_path, 'data',
                                   'tek_data', 'temperature.csv')
    temperature = pd.read_csv(input_temp_path)['temperature'].values
    # gen_heat_profile("Wohngebäude", 300, temperature, plot=True)
    gen_heat_profile("Verwaltungsgebäude", 300, temperature, plot=True)

    # print(calc_bld_demand("Wohngebäude (MFH)", 10000, 'heat',
    #                       energy_typ='gering'))
    # print(calc_bld_demand("Verwaltungsgebäude", 300, "elec"))

    # calc_residential_demand('EFH', 1968, 200)

    # weekday_lt = find_weekday(2022)
    # print(op_time_status(2022, 'Bettenzimmer'))
