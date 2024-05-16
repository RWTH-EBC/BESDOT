"""
Environment object storage the weather and price information. The weather data
could get from data/weather_data with the name of the city and year. Or it could
be given by the user in the instantiation of an Environment object.
"""
import os
import warnings
import pandas as pd

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

    def __init__(self, weather_file=None, city='Dusseldorf', year=2021,
                 start_time=0, time_step=8760):
        self.city = city
        self.year = year
        # start_time: Start time of the optimization process to be
        # considered, in hours.
        # time_step: The number of steps to be considered in the optimization
        # process, in hours .
        # should be from 1 to 8759, start_time
        # should be from 0 to 8759, and the sum of both should be from 1 to
        # 8760.
        self.start_time = start_time
        self.time_step = time_step
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
        self.elec_price = 0.32  # €/kWh #0.3, 0.37
        self.gas_price = 0.07  # €/kWh #0.1, 0.1377
        self.heat_price = 0.08  # €/kWh
        self.heat_price_hub = 0.03  # €/kWh, production cost for energy hub
        self.elec_feed_price = 0.08  # €/kWh #0.1, 0.05
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
