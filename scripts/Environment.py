"""
Environment object storage the weather and price information. The weather data
could get from data/weather_data with the name of the city and year. Or it could
be given by the user in the instantiation of an Environment object.
"""
import os
import warnings
import pandas as pd

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
city_info_file = os.path.join(base_path, "data", "subsidy", "city_state_country_info.csv")
weather_data_path = os.path.join(base_path, "data", "weather_data")
Soil_temperature_path = os.path.join(base_path, "data", "weather_data",
                                     "Dusseldorf", "soil_temp.csv")


def _read_weather_file(weather_file=None, city='Dusseldorf', year=2021):
    if weather_file is None:
        weather_dir = os.path.join(weather_data_path, city)
        if year < 2025:
            for file in os.listdir(weather_dir):
                if file.startswith("TRY2015") and file.endswith("Jahr.dat"):
                    weather_file = os.path.join(weather_dir, file)
        else:
            for file in os.listdir(weather_dir):
                if file.startswith("TRY2045") and file.endswith("Jahr.dat"):
                    weather_file = os.path.join(weather_dir, file)
    else:
        # even if city and year is given, the provided weather file has
        # higher priority than DWD file.
        pass

    soil_data = None

    if year < 2025:
        weather_profile = pd.read_table(weather_file, skiprows=33, sep='\t')
        soil_data = pd.read_csv(Soil_temperature_path)
    else:
        weather_profile = pd.read_table(weather_file, skiprows=35, sep='\t')
    temperature_profile = weather_profile.iloc[:, 0].str.split('\s+', 17).str[
        5].astype('float64').values
    wind_profile = weather_profile.iloc[:, 0].str.split('\s+', 17).str[
        8].astype('float64').values
    direct_solar_profile = weather_profile.iloc[:, 0].str.split('\s+', 17).str[
        12].astype('float64').values
    diffuse_solar_profile = weather_profile.iloc[:, 0].str.split('\s+', 17).str[
        13].astype('float64').values
    total_solar_profile = diffuse_solar_profile + direct_solar_profile

    soil_temperature_profile = soil_data.loc[:, 'temperature'].values.tolist()

    return temperature_profile, wind_profile, total_solar_profile, \
           soil_temperature_profile


class Environment(object):

    def __init__(self, weather_file=None, city='Lindenberg', year=2021,
                 start_time=0, time_step=8760, user=None, conditions=None):
        city_info = pd.read_csv(city_info_file)
        city_row = city_info[city_info['City'] == city]
        if not city_row.empty:
            self.city = city_row.iloc[0]['City']
            self.state = city_row.iloc[0]['State']
            self.country = city_row.iloc[0]['Country']
        else:
            warnings.warn(f"City {city} not found in city_info.csv. Using default values.")
            self.city = 'Lindenberg'
            self.state = 'Bayern'
            self.country = 'Germany'
        # start_time: Start time of the optimization process to be
        # considered, in hours.
        # time_step: The number of steps to be considered in the optimization
        # process, in hours .
        # should be from 1 to 8759, start_time
        # should be from 0 to 8759, and the sum of both should be from 1 to
        # 8760.
        self.year = year
        self.start_time = start_time
        self.time_step = time_step
        self.user = user
        self.conditions = conditions
        if start_time + time_step <= 0:
            warnings.warn('The selected interval is too small or the start '
                          'time is negative')
        elif start_time + time_step > 8760:
            warnings.warn('The selected interval is too large or the time '
                          'selected is across the year')

        # todo: the default value should be check with the aktuell data and
        #  add source.
        # todo (yni): price could be set into series, array or list,
        #  for variable price
        # https://www.finanztip.de/stromvergleich/strompreis/
        self.elec_price = 0.38  # €/kWh #0.3, 0.37, the price of buying electricity,
                                # average in 2024
                                # https://www.verivox.de/strom/strompreise/
        self.elec_price_pump = 0.30 # yso: 20 percent cheaper than normal household electricity
                                    # https://www.verivox.de/heizstrom/waermepumpe/
        self.elec_price_hub = 0.17 # €/kWh, Average industrial electricity prices in 01/2024
                                   # https://www.eon.de/de/gk/strom/industriestrom.html
        self.elec_feed_price = 0.08  # €/kWh #0.1, 0.05, Feed-in tariff 2024
                                     # https://senec.com/de/magazin/einspeiseverguetung
        self.gas_price = 0.11  # €/kWh #0.1, 0.1377, Average in 2024
                               # https://www.verivox.de/gas/gaspreisentwicklung/
        self.gas_price_hub = 0.08 # €/kWh, production cost for energy hub, Q1 2024
                                  # https://de.statista.com/statistik/daten/studie/
                                  # 168528/umfrage/gaspreise-fuer-gewerbe-und-industriekunden
                                  # -seit-2006/
        self.heat_price = 0.14  # €/kWh, the price for buying heat from the heat network
                                # https://www.stadtwerke-fellbach.de/de/Waerme/Waermepreise/
                                # Waermepreise/Waermepreise-2024-ab-01.04.-19-.pdf
        self.heat_price_hub =0.03 # hub暂时不需要买热
        self.elec_emission = 397  # g/kWh
        self.gas_emission = 202  # g/kWh
        self.co2_price = 35  # €/t

        # Read the weather file in the directory "data"
        # The parameter with suffix '_whole' are the parameter for the whole
        # year and without suffix '_whole' are slice for given time steps.
        temp_profile, wind_profile, irr_profile, soil_temperature_profile = \
            _read_weather_file(weather_file, city, year)
        self.temp_profile_whole = temp_profile
        self.wind_profile_whole = wind_profile
        self.irr_profile_whole = irr_profile
        self.soil_temperature_profile_original = soil_temperature_profile
        self.temp_profile = temp_profile[start_time:start_time + time_step]
        self.wind_profile = wind_profile[start_time:start_time + time_step]
        self.irr_profile = irr_profile[start_time:start_time + time_step]
        self.soil_temperature_profile = soil_temperature_profile[
                                        start_time: start_time + time_step]
        # The following slice for temperatur profile is set a virtual
        # temperature so that there is no heat demand in summer when
        # calculating heat demand. The hard coded value for 3624 means day
        # 151, which represents 1. Juni; the last time in slice 5832 means
        # day 243, which represents 31. August.
        # Attention!!! The use of this method is very likely to
        # have a significant impact on other equipment (air source heat
        # pumps, solar thermal). Special care needs to be taken when using
        # this method.

        # temp_profile[3624:5832] = 30
