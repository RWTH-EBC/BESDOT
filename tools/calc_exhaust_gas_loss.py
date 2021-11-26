import pandas as pd
import os
from warnings import warn
import numpy as np

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(base_path, "data", "component_database",
                               "GasBoiler", "BOI_exhaust_gas.xlsx")


def calc_exhaust_gas_loss(path, file_name):
    data = pd.read_excel(path, sheet_name='INPUT')
    df = pd.DataFrame(columns=['exhaustgastemp', 'airtemp', 'A1', 'B', 'C', 'H',
                               'O', 'N', 'airnumber', 'v0', 'vCO2',
                               'vexhaustgas',
                               'vCO2_pre', 'exhaustgasloss'], index=[])
    airnumber_1 = 0
    for i in range(len(data)):
        a = data.iloc[i]
        v0 = (1/0.21)*(1.866*a['C']+5.56*a['H']-0.7*a['O'])
        a['v0'] = v0
        vCO2 = a['C'] * 1.866
        a['vCO2'] = vCO2
        if a['airnumber'] == 1:
            airnumber_1 = vCO2+(0.79*v0+0.8*a['N'])+(11.1*a['H']+0.016*v0)
            vexhaustgas = vCO2+(0.79*v0+0.8*a['N'])+(11.1*a['H']+0.016*v0)
        if a['airnumber'] != 1:
            vexhaustgas = airnumber_1 + (a['airnumber']-1) * a['v0'] + 0.016 * \
                     (a['airnumber']-1) * a['v0']
        a['vexhaustgas'] = vexhaustgas
        vCO2_pre = vCO2/vexhaustgas
        a['vCO2_pre'] = vCO2_pre
        exhaustgasloss = (a['exhaustgastemp']-a['airtemp'])*(a['A1']/(
                vCO2_pre*100) + a['B'])
        a['exhaustgasloss'] = exhaustgasloss
        size = df.index.size
        df.loc[size] = [a['exhaustgastemp'], a['airtemp'], a['A1'], a['B'],
                        a['C'], a['H'], a['O'], a['N'], a['airnumber'], a['v0'],
                        a['vCO2'], a['vexhaustgas'], a['vCO2_pre'],
                        a['exhaustgasloss']]
    df.to_excel(file_name, sheet_name='OUTPUT')


calc_exhaust_gas_loss(path, "BOI_exhaust_gas_loss.xlsx")


