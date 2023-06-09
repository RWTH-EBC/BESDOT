"""This tool is designed to calculate the temperature at a depth of 1m in the soil."""
import pandas as pd
import os
import math
import utils.post_processing as post_pro
from warnings import warn
import numpy as np

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_path = os.path.join(base_path, "data", "weather_data",
                           "Dusseldorf", "type_temp.csv")


Tsoil = {}
def calc_soil_temp():
    for t in range(0, 8760):
        a = (t+1) % 24
        if 11 < a < 21:
            b = 10
        else:
            b = 5
        Tsoil[t + 1] = b
    data = pd.DataFrame(Tsoil.items(), columns=['time', 'temperature'])
    data.to_csv(output_path)
    soil_temperature_profile = data.loc[:, 'temperature']
    # b = soil_temperature_profile.values.tolist()
    # post_pro.plot_temp('type_temperature', b)
    c = 12 % 24
    print(c)


if __name__ == "__main__":
    calc_soil_temp()

