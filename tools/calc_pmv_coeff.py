import os
import pandas as pd

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
weather_data_path = os.path.join(base_path, "data", "weather_data")
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_path = os.path.join(base_path, "data", "weather_data",
                           "Dusseldorf", "pmv_coeff.csv")


def read_weather_file(weather_file=None, city='Dusseldorf', year=2021):
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
    h = weather_profile.iloc[:, 0].str.split('\s+', 17).str[
        4].astype('float64').values
    m = weather_profile.iloc[:, 0].str.split('\s+', 17).str[
        2].astype('float64').values

    return h, m


Icl = {}


def calc_soil_temp(st, mo):
    Icl1 = [0.2803, 0.1717, 7.1383]
    Icl2 = [0.1383, 0.0269, 3.0190]
    Icl3 = [0.1478, -0.1371, 2.5239]
    # print(Icl1[1])

    for t in range(0, 8760):
        if 3 < mo[t] < 9:
            if 9 < st[t] < 24:
                Icl[t] = Icl1
            else:
                Icl[t] = Icl2
        else:
            if 9 < st[t] < 24:
                Icl[t] = Icl2
            else:
                Icl[t] = Icl3
        #print(Icl[t+1][1])

    data = pd.DataFrame(Icl.items(), columns=['time', 'coeff'])
    #print(data)
    data.to_csv(output_path)
    '''soil_temperature_profile = data.loc[:, 'temperature']
    b = soil_temperature_profile.values.tolist()
    post_pro.plot_temp('soil_temperature', b)'''


if __name__ == "__main__":
    h, m = read_weather_file(weather_file=None, city='Dusseldorf', year=2021)
    calc_soil_temp(h, m)
    data = pd.read_csv(output_path)
    pmv = data.loc[:, 'coeff']
    b = pmv.values.tolist()
    output = eval(b[1])
    print(output[1])
