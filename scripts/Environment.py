"""
Environment object saves the parameter information for optimization model. The
weather data could get from data/weather_data with the name of the city and
year. Or it could be given by the user in the instantiation of an Environment
object.
"""
import os
import warnings
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

    if year < 2025:
        weather_profile = pd.read_table(weather_file, skiprows=33, sep='\t')
    else:
        weather_profile = pd.read_table(weather_file, skiprows=35, sep='\t')
    temperature_profile = weather_profile.iloc[:, 0].str.split('\s+').str[
        5].astype('float64').values
    wind_profile = weather_profile.iloc[:, 0].str.split('\s+').str[
        8].astype('float64').values
    direct_solar_profile = weather_profile.iloc[:, 0].str.split('\s+').str[
        12].astype('float64').values
    diffuse_solar_profile = weather_profile.iloc[:, 0].str.split('\s+').str[
        13].astype('float64').values
    total_solar_profile = diffuse_solar_profile + direct_solar_profile

    return temperature_profile, wind_profile, total_solar_profile


# The following function is used to read the soil temperature profile. The
# profile should be given by the user. If not, the default profile is used.
# todo: the value of soil temperature should be simulated with the city or
#  from weather data.
def _read_soil_temperature_file(soil_temperature_file=None):
    if soil_temperature_file is None:
        soil_temperature_file = os.path.join(base_path, "data", "weather_data",
                                             "Dusseldorf", "soil_temp.csv")
    soil_data = pd.read_csv(soil_temperature_file)
    soil_temperature_profile = soil_data.loc[:, 'temperature'].values.tolist()
    return soil_temperature_profile


# Calculate the temperature at a depth of 1m in the soil. This function
# should be fixed up in the future with a given weather data.
def _calc_soil_temp():
    """
    The formulas for soil temperature and soil heat radiation are from the paper
    "Ground Thermal Diffusivity Calculation by Direct Soil Temperature
    Measurement. Application to very Low Enthalpy Geothermal Energy Systems".
    Relevant temperature data from kachelmannwetter measurements.
    w——Angular frequency (rad/s). The rate of change of the function argument in
    units of radians per second.
    Tm——Annual average temperature of soil in the stable layer
    Th——maximum temperatures of the soil
    Tp——Amplitude ( ̋C); the peak deviation of the function from zero
    z——the depth (m)
    a——the ground thermal diffusivity (m2/s)
    Tsoil——Soil temperature at a certain depth
    """
    import math
    w = 1.99e-7
    Tm = 12.38
    Th = 20.06
    Tp = 10.67
    z = 1
    a = w / 2 * (1 / math.log(Tp / (Th - Tm))) ** 2
    Tsoil = {}
    for t in range(0, 8760):
        Tsoil[t + 1] = Tm - Tp * math.exp(-z * (w / (2 * a)) ** 0.5) * math.cos(
            2 * math.pi / 8760 * (t + 1 - 414))

    data = pd.DataFrame(Tsoil.items(), columns=['time', 'temperature'])
    soil_temperature_profile = data.loc[:, 'temperature']
    return soil_temperature_profile


# The following function is used to find the state and country of the city.
def _find_state_country(city):
    city_info_file = os.path.join(base_path, "data", "subsidy",
                                  "city_state_country_info.csv")
    city_info = pd.read_csv(city_info_file)
    city_row = city_info[city_info['City'] == city]
    if not city_row.empty:
        state = city_row.iloc[0]['State']
        country = city_row.iloc[0]['Country']
    else:
        warnings.warn(f"City {city} not found in city_info.csv. "
                      f"Using default values.")
        state = 'Bayern'
        country = 'Germany'
    return state, country


class Environment(object):

    def __init__(self, weather_file=None, city='Dusseldorf', year=2021,
                 start_time=0, time_step=8760, user=None, conditions=None):
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

        self.city = city
        self.state, self.country = _find_state_country(city)
        self.user = user
        self.conditions = conditions
        if start_time + time_step <= 0:
            warnings.warn('The selected interval is too small or the start '
                          'time is negative')
        elif start_time + time_step > 8760:
            warnings.warn('The selected interval is too large or the time '
                          'selected is across the year')

        # todo: the default value should be check with the actual data and
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
        self.biomass_price = 0.02  # €/kWh

        self.elec_emission = 397  # g/kWh
        self.gas_emission = 202  # g/kWh
        self.co2_price = 35  # €/t

        # Read the weather file in the directory "data"
        # The parameter with suffix '_whole' are the parameter for the whole
        # year and without suffix '_whole' are slice for given time steps.
        temp_profile, wind_profile, irr_profile = \
            _read_weather_file(weather_file, city, year)
        soil_temperature_profile = _read_soil_temperature_file()
        self.temp_profile_whole = temp_profile
        self.wind_profile_whole = wind_profile
        self.irr_profile_whole = irr_profile
        self.soil_temperature_profile_original = soil_temperature_profile
        self.temp_profile = temp_profile[start_time:start_time + time_step]
        self.wind_profile = wind_profile[start_time:start_time + time_step]
        self.irr_profile = irr_profile[start_time:start_time + time_step]
        self.soil_temperature_profile = soil_temperature_profile[
                                        start_time: start_time + time_step]

        # The following slice for temperature profile is set a virtual
        # temperature so that there is no heat demand in summer when
        # calculating heat demand. The hard coded value for 3624 means day
        # 151, which represents 1. June; the last time in slice 5832 means
        # day 243, which represents 31. August.
        # Attention!!! The use of this method is very likely to
        # have a significant impact on other equipment (air source heat
        # pumps, solar thermal). Special care needs to be taken when using
        # this method.

        # temp_profile[3624:5832] = 30
