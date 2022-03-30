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
input_profile_path = os.path.join(base_path, "data", "tek_data",
                                  "DHW_profile.xlsx")
input_energy_path = os.path.join(base_path, "data", "tek_data",
                                 "TEK_Teilenergiekennwerte.xlsx")
input_zone_path = os.path.join(base_path, "data", "tek_data",
                               "GHD_Zonierung.xlsx")
input_tabula_path = os.path.join(base_path, "data", "tek_data",
                                 "TABULA_data.xlsx")
output_path = os.path.join(base_path, "data", "tek_data",
                           "output_hot_water_profile")


def gen_hot_water_profile(building_typ,
                          area,
                          energy_typ="mittel",
                          plot=False,
                          save_plot=False):
    bld_hot_water_demand = calc_bld_demand(building_typ, area, energy_typ)
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

    '''
    for row in range(len(hot_water_df)):
        total_hot_water_profile = hot_water_df.loc[
            row, 'Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)']

    if plot:
        plot_profile(total_hot_water_profile, save_plot)
    '''

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


def calc_bld_demand(building_typ, area, energy_typ='mittel'):
    # Analysis thermal zones in building
    new_zone_df = analysis_bld_zone(building_typ, area)

    bld_demand = 0
    demand_df = pd.read_excel(input_energy_path, sheet_name=energy_typ)
    for row in range(len(new_zone_df)):
        zone = new_zone_df.loc[row, 'DIN_Zone']
        zone_area = new_zone_df.loc[row, 'new_area']
        zone_demand = calc_zone_demand(demand_df, zone, zone_area)
        bld_demand += zone_demand

    return bld_demand


def calc_zone_demand(demand_df, zone_typ, zone_area):
    """Calculate the annual total hot water demand for each zone"""
    total_demand = 0  # Unit kWh
    column_name = 'Warmwasser'
    zone_demand = demand_df[demand_df['Standard-Nutzungseinheiten'] ==
                            zone_typ][column_name].values[0]
    total_demand += zone_demand * zone_area

    return total_demand


def plot_profile(heat_profile, save_plot=False):
    plt.figure()
    plt.plot(heat_profile)
    plt.ylabel('Hot Water Profile')
    plt.xlabel('Hours [h]')
    plt.ylim(ymin=0)
    plt.xlim(xmin=0)
    plt.grid()
    if save_plot:
        plt.savefig(os.path.join(output_path, 'hot_water_profile_figure.jpg'))
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
    # calc_total_demand("Verwaltungsgebäude", "mittel", 10000)
    # gen_hot_water_profile("Verwaltungsgebäude", 300, plot=True)
    # print(calc_bld_demand("Verwaltungsgebäude", 300))
    calc_residential_demand('EFH', 1968, 200)
