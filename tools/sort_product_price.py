"""
This module takes out the information from collected price tables and sort
them into the formate, which could be used in use cases. The overview table
is divided into multiple tables, which contain the with-fix-cost model,
only-specific-cost model and price points for each product. The file name
of these tables would be generated with its type and

"""

import os
import warnings
import shutil
import pandas as pd
import tools.get_all_class as gac

base_path = os.path.dirname(os.path.dirname(__file__))
component_path = os.path.join(base_path, "data", "component_database")
price_path = os.path.join(base_path, "data", 'prices')

match_dict = {'HeatExchangerFluid': None,
              'Radiator': 'Radiators',
              'CondensingBoiler': 'Gas_heating',
              'GasBoiler': 'Gas_heating',
              'UnderfloorHeat': 'Underfloor_heating',
              'ElectricityGrid': None,
              'CHP': None,
              'CHPFluidBig': None,
              'HeatExchanger': 'Home_station',
              'ElectricalConsumption': None,
              'HomoStorage': 'Storage_technology',
              'HotWaterStorage': 'Storage_technology',
              'ElectricRadiator': None,
              'StratificationStorage': 'Storage_technology',
              'HeatPump': 'Heat_pumps',
              'HeatPumpFluid': 'Heat_pumps',
              'Battery': None,
              'Storage': None,
              'StandardBoiler': 'Gas_heating',
              'CHPFluidSmall': None,
              'HotWaterConsumption': None,
              'GasGrid': None,
              'HeatPumpQli': None,
              'HotWaterConsumptionFluid': None,
              'ElectricityMeter': None,
              'HeatConsumption': None,
              'HeatConsumptionFluid': None,
              'HeatGrid': None,
              'SolarThermalCollector': 'Solar_technology',
              'ElectricBoiler': 'Flow_heater-electricity',
              'GasHeatPump': None,
              'CHPFluidSmallHi': None,
              'SolarThermalCollectorFluid': 'Solar_technology',
              'ThreePortValve': None,
              'GroundHeatPumpFluid': 'brine-water',
              'ThroughHeaterElec': 'Flow_heater-electricity',
              'HeatExchangerFluid_Solar': None,
              'PV': None,
              'HeatGridFluid': None,
              'AirHeatPumpFluid': 'air-water'}


def read_table(table_name=None):
    """Read the table"""
    if table_name is not None:
        table_path = os.path.join(price_path, table_name)
    else:
        # todo: the latest table in folder component_database should be got,
        #  if no table name is given.
        table_path = os.path.join(price_path,
                                  "total_cost_overview_20220921-18_53_02.csv")

    whole_table = pd.read_csv(table_path)
    return whole_table


def generate_tables(dataframe):
    """Generate a table for each sub technology. Only the latest price
    information would be used. The column name of original crawler table are
    rewritten for better understanding"""
    # Sorting rows according to date, so that if the old data would be in the
    # end of the dataframe and could be ignored, if the table for same type
    # components is already generated. Table list is used to store the name of
    # already generated tables.
    dataframe = dataframe.sort_values(by=['Datetime'], ascending=False)
    table_list = []

    for index, row in dataframe.iterrows():
        table_name = row['Manufacturer']
        if row['Basic technology'] != "-" and row['Basic technology'] is not \
                None:
            table_name += "-"
            table_name += row['Basic technology']
        if row['Specified technology'] != "-" and row['Specified technology'] \
                is not None:
            table_name += "-"
            table_name += row['Specified technology']
        if row['Addition'] != "-" and row['Addition'] is not None:
            table_name += "-"
            table_name += row['Addition']

        if table_name not in table_list:
            # Remove unwanted columns. The wanted columns are:
            # only-unit-price, fixed-price, fixed-unit-price, data-pair
            df = row.to_frame().T
            df = df.rename(columns={'m_1': 'fixed-unit-price'})
            df = df.rename(columns={'n': 'fixed-price'})
            df = df.rename(columns={'m_2': 'only-unit-price'})
            df = df.rename(columns={'Data pairs': 'data-pair'})
            df = df.drop(columns=['Unnamed: 0', 'Manufacturer',
                                  'Basic technology', 'Specified technology',
                                  'Addition', 'y_1 = m_1x + n', 'R_1²',
                                  'y_2 = m_2x', 'R_2²', 'Size database',
                                  'Datetime'])

            # Generate table
            table_path = os.path.join(price_path, table_name + '.csv')
            df.to_csv(table_path)
        else:
            # Since the rows are sorted with date, the old data would not be
            # considered.
            pass

    pass


def check_price_table(dataframe):
    """Check the technologies in dataframe and developed models in this
    project, if find unmatched item, raise a warning."""
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
    basic_tech_list = dataframe["Basic technology"].drop_duplicates().tolist()
    spec_tech_list = dataframe["Specified technology"].drop_duplicates().tolist()
    addi_tech_list = dataframe["Addition"].drop_duplicates().tolist()

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


def sort_table():
    """Sorting all tables in folder 'prices' and put them into the
    corresponding folders in database.
    Attention! This method is hard-coded, since the formate of crawler table
    is fixed. If the crawler table is changed, this method should be modified
    as well.
    """
    for component in os.listdir(component_path):
        if component in match_dict.keys():
            if match_dict[component] is not None:
                for table in os.listdir(price_path):
                    if match_dict[component] in table:
                        # print('find price for', component, ',table name is',
                        #       table)
                        table_path = os.path.join(price_path, table)
                        table_database_path = os.path.join(component_path,
                                                           component, table)
                        shutil.copy(table_path, table_database_path)
        else:
            warn_msg = 'Find a new component ' + component + \
                       ', which is not considered in ' \
                       'tools.sort_product_price. Please update ' \
                       'the method again.'
            warnings.warn(warn_msg)

    # print(os.listdir(price_path))


def enrich_table():
    """
    Enriching the tables from prices folder, which contains only price
    information, other important data should be taken from a raw data sheet.
    """
    for component in os.listdir(component_path):
        if 'raw.csv' in os.listdir(os.path.join(component_path, component)):
            raw_df = pd.read_csv(os.path.join(component_path, component,
                                              'raw.csv'))
            for table in os.listdir(os.path.join(component_path, component)):
                print("===")
                print(component)
                print(table)
                if component in match_dict.keys():
                    if match_dict[component] is not None:
                        if match_dict[component] in table:
                            # Search the tables, which come from crawler
                            price_df = pd.read_csv(os.path.join(
                                component_path, component, table))
                            price_df = price_df.reset_index(drop=True)
                            enriched_df = pd.concat([price_df, raw_df], axis=1)
                            enriched_df.to_csv(os.path.join(
                                component_path, component, table))
                    else:
                        print("Doesn't find table from crawler in", component)
                else:
                    warn_msg = 'Find a new component ' + component + \
                               ', which is not considered in ' \
                               'tools.sort_product_price. Please update ' \
                               'the method again.'
                    warnings.warn(warn_msg)
        else:
            warn_msg = 'Find a new component database' + component + \
                       ', which does not contain a raw data sheet. ' \
                       'Please check the database again.'
            warnings.warn(warn_msg)


def trim_data():
    """temporary method, which would be removed later. Some raw sheet
    contains old data, which would not be used in the tool. These old data
    should be deleted from the files. This method should be done with the
    development of the method read_property() of each model."""
    pass


if __name__ == "__main__":
    # Take the data from the latest crawler table and save them in individual
    # tables.
    # price_df = read_table()
    # generate_tables(price_df)

    # Check the table, if necessary. Not necessary.
    # check_price_table(price_df)

    # Last step to generate the csv files, which could be used in optimization
    # sort_table()
    # enrich_table()
    trim_data()
