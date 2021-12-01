"""This tool is used to calculate the exhaust gas loss of gasboiler"""
import pandas as pd
import os
from warnings import warn
import numpy as np

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(base_path, "data", "component_database",
                               "GasBoiler", "BOI1_exhaust_gas.csv")
output_path = os.path.join(base_path, "data", "component_database",
                               "GasBoiler", "BOI1_exhaust_gas_loss.csv")

"""exhaustgastemp[°C]: the temperature of the exhaust gas in the boiler.
   air temperature[°C]: usually assumed to be 25 degrees.
   C,H,N,O[%]: the mass ratios of carbon, hydrogen, oxygen and nitrogen in 
   natural gas.
   airratio: less than 1 for insufficient combustion, equal to 1 for sufficient 
   combustion and greater than 1 for excess combustion.
   v0[m³/kg]: the theoretical amount of air required for the complete combustion 
   of 1kg of natural gas,
              vO= (1/0.21)*(1.866*C+5.56*H-0.7*O)
   vCO2[m³/kg]: volume of carbon dioxide in exhaustgas after combustion, 
                vCO2=1.866*C
   vexhaustgas[m³/kg]: theoretical exhaustgas volume after combustion
       if airratio = 1, vexhaustgas=vCO2+(0.79*v0+0.8*N)+(11.1*H+0.016*v0)
       if airratio > 1, vexhaustgas=vexhaustgas(airratio=1)+(airratio-1)*v0+
       0.016*(airratio-1)*v0
   vCO2_pre[%]: a percentage of carbon dioxide volume and total flue gas volume
   
"""
def calc_exhaust_gas_loss(path, file_name):
    data = pd.read_csv(path)
    df = pd.DataFrame(columns=['exhaustgastemp', 'airtemp', 'A1', 'B', 'C', 'H',
                               'O', 'N', 'airratio', 'v0', 'vCO2',
                               'vexhaustgas',
                               'vCO2_pre', 'exhaustgasloss'], index=[])
    for i in range(len(data)):
        a = data.iloc[i]
        v0 = (1/0.21)*(1.866*a['C']+5.56*a['H']-0.7*a['O'])
        a['v0'] = v0
        vCO2 = a['C'] * 1.866
        a['vCO2'] = vCO2
        vexhaustgas_1 = vCO2+(0.79*v0+0.8*a['N'])+(11.1*a['H']+0.016*v0)
        if a['airratio'] == 1:
            vexhaustgas = vexhaustgas_1
        if a['airratio'] != 1:
            vexhaustgas = vexhaustgas_1 + (a['airratio']-1) * v0 + 0.016 * \
                     (a['airratio']-1) * v0
        a['vexhaustgas'] = vexhaustgas
        vCO2_pre = vCO2/vexhaustgas
        a['vCO2_pre'] = vCO2_pre
        exhaustgasloss = (a['exhaustgastemp']-a['airtemp'])*(a['A1']/(
                vCO2_pre*100) + a['B'])
        a['exhaustgasloss'] = exhaustgasloss
        size = df.index.size
        df.loc[size] = [a['exhaustgastemp'], a['airtemp'], a['A1'], a['B'],
                        a['C'], a['H'], a['O'], a['N'], a['airratio'], a['v0'],
                        a['vCO2'], a['vexhaustgas'], a['vCO2_pre'],
                        a['exhaustgasloss']]
    df.to_csv(output_path)
calc_exhaust_gas_loss(path, 'BOI1_exhaust_gas_loss.csv')


'''def get_properties(path, file_name):
    model_property_file = os.path.join(base_path, "data", "component_database",
                               "GasBoiler", "BOI_exhaust_gas.csv")
    properties = pd.read_csv(model_property_file)
    return properties


def _read_properties(properties):
     if 'exhaustgastemp' in properties.columns:
         self.exhaustgastemp = float(properties['exhaustgastemp'])
     if 'airtemp' in properties.columns:
         self.airtemp = float(properties['airtemp'])
     if 'A1' in properties.columns:
         self.A1 = float(properties['A1'])
     if 'B' in properties.columns:
         self.B = float(properties['B'])
     if 'C' in properties.columns:
         self.C = float(properties['C'])
     if 'H' in properties.columns:
         self.H = float(properties['H'])
     if 'O' in properties.columns:
         self.O = float(properties['O'])
     if 'N' in properties.columns:
         self.N = float(properties['N'])
     if 'airnumber' in properties.columns:
         self.airnumber = float(properties['airnumber'])
     v0 = (1 / 0.21) * (1.866 * self.C + 5.56 * self.H - 0.7 * self.O)
     vCO2 = self.C * 1.866
     if self.airnumber == 1:
         self.airnumber = vCO2 + (0.79 * v0 + 0.8 * self.N) + (
                 11.1 * self.H + 0.016 * v0)
         vexhaustgas = vCO2 + (0.79 * v0 + 0.8 * self.N) + (
                 11.1 * self.H + 0.016 * v0)
     if self.airnumber != 1:
         vexhaustgas = airnumber_1 + (self.airnumber - 1) * v0 + 0.016 * \
                       (self.airnumber - 1) * v0
     vCO2_pre = vCO2 / vexhaustgas
     exhaustgasloss = (self.exhaustgastemp - self.airtemp) * (self.A1 / (
             vCO2_pre * 100) + self.B)
     print(exhaustgasloss)
     return exhaustgas

def calc_exhaust_gas_loss(self):
    v0 = (1 / 0.21) * (1.866 * self.C + 5.56 * self.H - 0.7 * self.O)
    vCO2 = self.C * 1.866
    if self.airnumber == 1:
        self.airnumber = vCO2 + (0.79 * v0 + 0.8 * self.N) + (
                    11.1 * self.H + 0.016 * v0)
        vexhaustgas = vCO2 + (0.79 * v0 + 0.8 * self.N) + (
                    11.1 * self.H + 0.016 * v0)
    if self.airnumber != 1:
        vexhaustgas = airnumber_1 + (self.airnumber - 1) * v0 + 0.016 * \
                      (self.airnumber - 1) * v0
    vCO2_pre = vCO2 / vexhaustgas
    exhaustgasloss = (self.exhaustgastemp - self.airtemp) * (self.A1 / (
            vCO2_pre * 100) + self.B)
    print(exhaustgasloss)
    return exhaustgas
calc_exhaust_gas_loss()'''


