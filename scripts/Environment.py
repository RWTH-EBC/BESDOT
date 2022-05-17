"""
Environment object storage the weather and price information. The weather data
could get from data/weather_data with the name of the city and year. Or it could
be given by the user in the instantiation of an Environment object.
"""
import os
import pandas as pd

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
weather_data_path = os.path.join(base_path, "data", "weather_data")


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

    return temperature_profile, wind_profile, total_solar_profile


class Environment(object):
    # start_time,end_time: data can be saved from start_time until end_time.
    # time_step should be from 1 to 8759, start_time should be from 0 to 8759,
    # and the sum of both should be from 1 to 8760.
    def __init__(self, weather_file=None, city='Dusseldorf', year=2021,
                 start_time=0, time_step=8760):
        self.city = city
        self.year = year
        self.start_time = start_time
        self.time_step = time_step
        # todo (yni): the default value should be check with the aktuell data
        # todo (yni): price could be set into series or list, for exchanger
        #  price
        self.elec_price = 3000  # €/kWh #0.3
        self.gas_price = 0.1  # €/kWh #0.1
        self.heat_price = 0.08  # €/kWh
        self.elec_feed_price = 0.1  # €/kWh
        self.elec_emission = 397  # g/kWh
        self.gas_emission = 202  # g/kWh
        self.co2_price = 35  # €/t

        # Read the weather file in the directory "data"
        # todo (yca): add comment for new variables
        temp_profile, wind_profile, irr_profile = _read_weather_file(
            weather_file, city, year)
        self.temp_profile_original = temp_profile
        self.wind_profile_original = wind_profile
        self.irr_profile_original = irr_profile
        self.temp_profile = temp_profile[start_time:start_time+time_step]
        self.wind_profile = wind_profile[start_time:start_time+time_step]
        self.irr_profile = irr_profile[start_time:start_time+time_step]
        temp_profile[3624:5832] = 30
