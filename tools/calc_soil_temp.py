"""This tool is designed to calculate the temperature at a depth of 1m in the soil."""
import pandas as pd
import os
import math
import tools.post_processing as post_pro
from warnings import warn
import numpy as np

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_path = os.path.join(base_path, "data", "weather_data",
                           "Dusseldorf", "soil_temp.csv")
"""
The formulas for soil temperature and soil heat radiation are from the paper 
"Ground Thermal Diffusivity Calculation by Direct Soil Temperature Measurement.
 Application to very Low Enthalpy Geothermal Energy Systems". Relevant 
 temperature data from kachelmannwetter measurements. 
w——Angular frequency (rad/s). The rate of change of the function argument in 
units of radians per second.
Tm——Annual average temperature of soil in the stable layer
Th——maximum temperatures of the soil
Tp——Amplitude ( ̋C); the peak deviation of the function from zero
z——the depth (m) 
a——the ground thermal diffusivity (m2/s)
Tsoil——Soil temperature at a certain depth
"""

Tsoil = {}
def calc_soil_temp():
    w = 1.99e-7
    Tm = 12.38
    Th = 20.06
    Tp = 10.67
    z = 1
    a = w / 2 * (1 / math.log(Tp / (Th - Tm))) ** 2
    #Tsoil = {}
    for t in range(0, 8760):
        Tsoil[t + 1] = Tm - Tp * math.exp(-z * (w / (2 * a)) ** 0.5) * math.cos(
            2 * math.pi / 8760 * (t + 1 - 414))

    data = pd.DataFrame(Tsoil.items(), columns=['time', 'temperature'])
    data.to_csv(output_path)
    soil_temperature_profile = data.loc[:, 'temperature']
    b = soil_temperature_profile.values.tolist()
    post_pro.plot_temp('soil_temperature', b)



if __name__ == "__main__":
    calc_soil_temp()

