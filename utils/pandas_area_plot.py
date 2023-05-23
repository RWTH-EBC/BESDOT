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


def plot_area(typ, resolution):
    """Plot the profile using pandas with engine matplotlib"""
    df = get_profile(typ, resolution)
    fig, ax = plt.subplots(1, 1)
    # df.plot.area(stacked=False)

    if typ == "Electricity":
        df.plot.area(ax=ax, format_string="y-.d",
                     color=['#beffd3', '#58b368', '#3e7d52'])
        plt.subplots_adjust(left=0.125)
    elif typ == "Heat":
        df.plot.area(ax=ax, format_string="r-.d",
                     color=['#ffcccc', '#ff9999', '#b36b6b'])
        plt.subplots_adjust(left=0.139)
    elif typ == "Cool":
        df.plot.area(ax=ax, format_string="b-.d",
                     color=['#cce5ff', '#6b8fb3', '#4b647d'])
    else:
        warn('This energy typ {} is not allowed'.format(energy))
        # warn('This energy typ %s is not allowed' % energy)

    if resolution == 'hour':
        pass
    elif resolution == 'day':
        ax.set_xlim(0, 365)
        ax.set_ylabel('Täglicher Energieverbrauch in kWh')
        ax.set_xlabel('Tag')
        ax.grid(axis="y", alpha=1)
        ax.set_axisbelow(True)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1])

    # plt.show()
    plot_path = os.path.join(OUTPUTS_PATH, energy + '.png')
    plt.savefig(plot_path)


if __name__ == '__main__':
    # for energy in ['Electricity', 'Heat', 'Cool']:
    for energy in ['Heat']:
        plot_area(energy, 'day')
