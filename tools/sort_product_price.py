"""
This module takes out the information from collected price tables and sort
them into the formate, which could be used in use cases.
"""

import os
import warnings
import pandas as pd
import tools.get_all_class as gac

base_path = os.path.dirname(os.path.dirname(__file__))
component_path = os.path.join(base_path, "data", "component_database")


def read_table(table_name=None):
    """Read the table"""
    if table_name is not None:
        table_path = os.path.join(component_path, table_name)
    else:
        # todo: the latest table in folder component_database should be got,
        #  if no table name is given.
        table_path = os.path.join(component_path,
                                  "total_cost_overview_20220921-18_53_02.csv")

    whole_table = pd.read_csv(table_path)
    return whole_table


def match_techs(price_df):
    """Match the techs in dataframe and developed models in this project."""
    # Default technologies list for checking match between models and prices
    # table
    default_tech_list = ['Air_conditioner', 'Flow_heater', 'Gas_heating',
                          'Heat_pumps', 'Home_station', 'Radiators',
                          'Solar_technology', 'Storage_technology',
                          'Underfloor_heating']
    default_spec_tech_list = ['boiler', 'therme', 'air-water', 'brine-water',
                              'compact_radiator', 'flat-plate_collectors',
                              'tube_collectors', 'buffer_storage',
                              'combined_storage', 'hot_water_storage']

    # Take out all the technologies in price table.
    basic_tech_list = price_df["Basic technology"].drop_duplicates().tolist()
    spec_tech_list = price_df["Specified technology"].drop_duplicates().tolist()
    addi_tech_list = price_df["Addition"].drop_duplicates().tolist()

    spec_tech_list.remove("-")
    addi_tech_list.remove("-")

    # Check the technologies in price table. Give a warn if unknown
    # technology is found.
    if set(basic_tech_list) <= set(default_tech_list):
        pass
    else:
        # miss_tech = basic_tech_list - default_tech_price
        warnings.warn("find missed basic technology in price table.")

    if set(spec_tech_list) <= set(default_spec_tech_list):
        pass
    else:
        # miss_tech = spec_tech_list - default_spec_tech_list
        warnings.warn("find missed specified technology in price table.")

    # default model list in 26.09.2022
    default_model_list = ['HeatExchangerFluid', 'Radiator',
                          'CondensingBoiler', 'GasBoiler', 'UnderfloorHeat',
                          'ElectricityGrid', 'CHP', 'CHPFluidBig',
                          'HeatExchanger', 'ElectricalConsumption',
                          'HomoStorage', 'HotWaterStorage', 'ElectricRadiator',
                          'StratificationStorage', 'HeatPump',
                          'HeatPumpFluid', 'Battery', 'Storage',
                          'StandardBoiler', 'CHPFluidSmall',
                          'HotWaterConsumption', 'GasGrid', 'HeatPumpQli',
                          'HotWaterConsumptionFluid', 'ElectricityMeter',
                          'HeatConsumption', 'HeatConsumptionFluid',
                          'HeatGrid', 'SolarThermalCollector',
                          'ElectricBoiler', 'GasHeatPump', 'CHPFluidSmallHi',
                          'SolarThermalCollectorFluid', 'ThreePortValve',
                          'GroundHeatPumpFluid', 'ThroughHeaterElec',
                          'HeatExchangerFluid_Solar', 'PV', 'HeatGridFluid',
                          'AirHeatPumpFluid']

    # Check the technologies in developed models. Give a warn if unknown
    # technology is found.
    model_list = gac.run().keys()
    if set(default_model_list) <= set(model_list):
        pass
    else:
        # miss_tech = basic_tech_list - default_tech_price
        warnings.warn("find missed model.")

    match_dict = {}

