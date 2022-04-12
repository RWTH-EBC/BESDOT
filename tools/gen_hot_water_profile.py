"""
This tool use the TEK project of IWU to calculate the annual energy demand of
the building and use the degree day method to generate the demand profile.
"""

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



