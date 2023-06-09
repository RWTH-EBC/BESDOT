"""This tool is used to calculate the energy loss of gas boiler because
of exhaust gas.
    exhaust_gas:temp[°C]: the temperature of the exhaust gas in the boiler.
    air_temperature[°C]: usually assumed to be 25 degrees.
    C,H,N,O[%]: the mass ratios of carbon, hydrogen, oxygen and nitrogen in
        natural gas.
    air_ratio: less than 1 for insufficient combustion, equal to 1 for
        sufficient combustion and greater than 1 for excess combustion.
    v0[m³/kg]: the theoretical amount of air required for the complete
        combustion of 1kg of natural gas, vO= (1/0.21)*(1.866*C+5.56*H-0.7*O)
    vCO2[m³/kg]: volume of carbon dioxide in exhaust_gas after combustion,
        vCO2=1.866*C
    v_exhaust_gas[m³/kg]: theoretical exhaust_gas volume after combustion
       if air_ratio = 1, v_exhaust_gas=vCO2+(0.79*v0+0.8*N)+(11.1*H+0.016*v0)
       if air_ratio > 1, v_exhaust_gas=v_exhaust_gas(air_ratio=1)+(
       air_ratio-1) *v0+0.016*(air_ratio-1)*v0
    vCO2_pre[%]: a percentage of carbon dioxide volume and total flue gas volume
"""
import pandas as pd
import os

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(base_path, "data", "component_database",
                               "GasBoiler", "BOI1_exhaust_gas.csv")
output_path = os.path.join(base_path, "data", "component_database",
                                      "GasBoiler", "BOI1_exhaust_gas_loss.csv")


def calc_exhaust_gas_loss(path, output_path):
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
    return exhaustgasloss
#calc_exhaust_gas_loss(path, output_path)





