import os
from warnings import warn
import pandas as pd
import matplotlib.pyplot as plt
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
INPUTS_PATH = os.path.join(BASE_PATH, 'inputs')
OUTPUTS_PATH = os.path.join(BASE_PATH, 'outputs')

def get_profile(typ, resolution):
    """Get the profile from file and return df in wanted resolution"""
    input_file = os.path.join(INPUTS_PATH, typ + '.xlsx')
    df = pd.read_excel(input_file)

    if resolution == "hour":
        pass
    elif resolution == "day":
        df_day = pd.DataFrame(columns=df.columns)
        for _ in range(len(df.index)):
            if _ % 24 == 0:
                df_day = df_day.append(pd.Series(), ignore_index=True)
                df_day.values[-1] = df.values[_]
            else:
                df_day.values[-1] += df.values[_]
        df = df_day
    else:
        warn('This resolution {} is not allowed!'.format(resolution))

    return df


def plot_area(typ, resolution, profile):
    """Plot the profile using pandas with engine matplotlib"""
    #df = get_profile(typ, resolution)
    #fig, ax = plt.subplots(1, 1)
    #df.plot.area(stacked=False)

    fig, ax = plt.subplots(1, 1)
    df = pd.DataFrame(profile)
    
    if typ == "Electricity":
        df.plot(color=['#beffd3'])
        plt.subplots_adjust(left=0.125)
        handles, labels = ax.get_legend_handles_labels()
        plt.legend(handles[::-1], labels[::-1], labels=['Electricity'],
                   loc='best')
        
    elif typ == "Heat":
        df.plot(color=['#ffcccc'])
        plt.subplots_adjust(left=0.139)
        handles, labels = ax.get_legend_handles_labels()
        plt.legend(handles[::-1], labels[::-1], labels=['Heat'],
                   loc='best')

    elif typ == "Cool":
        df.plot(color=['#cce5ff'])
        
    else:
        warn('This energy typ {} is not allowed'.format(energy))
        warn('This energy typ %s is not allowed' % energy)

    if resolution == 'hour':
        pass
    elif resolution == 'day':
           plt.title('Nachfrage des Energieverbrauchs in Stunde',fontsize=12,
                       color='black')

           plt.ylabel('Stündliche Energieverbrauch in kWh')
           plt.xlabel('Stunde')

    plt.show()
    #plot_path = os.path.join(OUTPUTS_PATH, energy + '.png')
    #plt.savefig(plot_path)





if __name__ == '__main__':
    # for energy in ['Electricity', 'Heat', 'Cool']:
    for energy in ['Heat']:
        plot_area(energy, 'day')
