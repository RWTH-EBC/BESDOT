"""
This tool use the TEK project of IWU to calculate the annual energy demand of
the building and use the degree day method to generate the demand profile.
"""

import os
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
input_profile_path = os.path.join(base_path, "data", "TEK_data",
                                  "GHD_profile.xlsx")
input_energy_path = os.path.join(base_path, "data", "TEK_data",
                                 "TEK_Teilenergiekennwerte.xlsx")
input_zone_path = os.path.join(base_path, "data", "TEK_data",
                               "GHD_Zonierung.xlsx")
output_path = os.path.join(base_path, "data", "TEK_data", "output_heat_profile")

# todo: The temperature profile should be taken from prosumer later
input_temp_path = os.path.join(base_path, "temperature.csv")


def gen_heat_profile(building_typ,
                     area,
                     temperature_profile,
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
        zone = new_zone_df.loc[row, 'DIN_Zone']
        zone_area = new_zone_df.loc[row, 'new_area']
        zone_heat_demand = calc_zone_demand(demand_df, 'heat', zone, zone_area)
        zone_heat_profile = degree_day(zone, zone_heat_demand, profile_df,
                                       temperature_profile)
        total_heat_profile = np.sum([total_heat_profile, zone_heat_profile],
                                    axis=0)
        total_heat_demand += zone_heat_demand

    if plot:
        plot_profile(total_heat_profile, save_plot)

    return total_heat_profile


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
               night_lower=False):
    heat_profile = []
    start_temp = 15  # The limit for heating on or off, could be the same as
    # set temperature? 15 comes from the german
    set_temp_heat = profile_df[profile_df['Raumtyp'] == zone_typ][
        'Raum-Solltemperatur_Heizung '].values[0]

    if night_lower:
        night_lower_temp(zone_typ, profile_df)
    else:
        total_degree_day = 0
        for temp in temperature_profile:
            if temp < start_temp:
                total_degree_day += (set_temp_heat - temp)

        for temp in temperature_profile:
            if temp < start_temp:
                heat_profile.append(
                    (set_temp_heat - temp) / total_degree_day * annual_value)
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


if __name__ == "__main__":
    # calc_total_demand("Verwaltungsgebäude", "mittel", 10000)
    # temperature = pd.read_csv(input_temp_path)['temperature'].values
    # gen_heat_profile("Verwaltungsgebäude", 300, temperature, plot=True)
    print(calc_bld_demand("Verwaltungsgebäude", 300, "elec"))
