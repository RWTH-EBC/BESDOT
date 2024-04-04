"""
This tool use the TEK project of IWU to calculate the annual energy demand of
the building and use the degree day method to generate the demand profile.
"""
import os
import datetime
from warnings import warn
import pandas as pd
import numpy as np

from utils.gen_heat_profile import calc_bld_demand
from utils.gen_heat_profile import analysis_bld_zone
from utils.gen_heat_profile import op_time_status

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

building_typ_dict_en = {"Administration building": "Verwaltungsgebäude",
                        "Office and service buildings":
                            "Büro und Dienstleistungsgebäude",
                        "University and research": "Hochschule und Forschung",
                        "Healthcare": "Gesundheitswesen",
                        "Educational facilities": "Bildungseinrichtungen",
                        "Cultural facilities": "Kultureinrichtungen",
                        "Sports facilities": "Sporteinrichtungen",
                        "Accommodation and catering":
                            "Beherbergen und Verpflegen",
                        "Commercial and industrial":
                            "Gewerbliche und industrielle",
                        "Retail premises": "Verkaufsstätten",
                        "Technical buildings": "Technikgebäude",
                        "Single-family house": "Wohngebäude",
                        "Multi-family house": "Wohngebäude (MFH)"}


def gen_hot_water_profile(building_typ_en, area, year=2021, energy_typ="mittel"):
    building_typ_de = building_typ_dict_en[building_typ_en]
    new_zone_df = analysis_bld_zone(building_typ_de, area)
    for row in range(len(new_zone_df)):
        zone = new_zone_df.loc[row, 'DIN_Zone']

    bld_hot_water_demand = calc_bld_demand(building_typ_en, area, 'hot_water', energy_typ)
    hot_water_heating_demand_df = pd.read_excel(input_profile_path, sheet_name='DHW', header=None, usecols=[1],
                                                skiprows=1)
    hot_water_heating_demand_df.columns = ['Wärmebedarf für Trinkwassererwärmung (kWh)']
    hot_water_heating_demand_df['Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'] = \
        hot_water_heating_demand_df['Wärmebedarf für Trinkwassererwärmung (kWh)'].map(
            lambda x: x / (4180 * 300 * (60 - 12) / 3600 / 1000 * 365) * bld_hot_water_demand)
    hot_water_heating_demand_array = np.array(
        hot_water_heating_demand_df['Aktueller Wärmebedarf für Trinkwassererwärmung (kWh)'])

    if building_typ_de == 'Verwaltungsgebäude':
        hour_status_array = np.array(op_time_status(year, zone))
        hot_water_heating_demand_array = np.multiply(hour_status_array, hot_water_heating_demand_array)

    return hot_water_heating_demand_array

