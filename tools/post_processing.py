"""
Tool to analyse the output csv from optimization
"""

import os
import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Attention! The elec_list and heat_list use the name from topology
# matrix, for different scenario the name for each component may change.
# Need to check for every scenario or fix the component name in topology.
elec_comp_list = ['heat_pump', 'pv', 'bat', 'e_grid', 'e_boi', 'e_cns',
                  'chp']
heat_comp_list = ['heat_pump', 'therm_cns', 'water_tes', 'solar_coll',
                  'boi', 'e_boi', 'chp']
elec_sink_tuple = ('heat_pump', 'bat', 'e_grid', 'e_boi')
heat_sink_tuple = 'water_tes'

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
opt_output_path = os.path.join(base_path, 'data', 'opt_output')

def plot_all(csv_file, time_interval):
    """

    Args:
        csv_file:
        time_interval: list, first element is the beginning time for plot and
        second element is the end time for plot
    """
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    size_dict = {}
    for element in elements_dict:
        if len(elements_dict[element]) == 1:
            if 'size' in element and not np.isnan(elements_dict[element][0]):
                size_dict[element] = elements_dict[element][0]
                print('The size of', element, 'is', size_dict[element])
        else:
            if sum(elements_dict[element]) > 0.001:
                plot_single(element, elements_dict[element][time_interval[0]:
                                                            time_interval[1]])

        #    fig, ax = plt.figure()
        #    ax = fig.add_subplot(111)
        #    ax1 = plot_single(element, elements_dict[element][time_interval[0]:
        #                                                      time_interval[1]])
        #    ax2 = ax1.twinx()
        #    ax2 = plot_single(element, elements_dict[element][time_interval[0]:
        #                                                      time_interval[1]])


            # print(element)
            # if element == 'heat_pump_water_tes':
            # plot_single(element, elements_dict[element])


def plot_single(name, profile):
    plot_output = os.path.join(opt_output_path, 'plot', 'Profile of ' + name)
    fig, ax = plt.subplots(figsize=(14, 14))
    #ax = fig.add_subplot(111)
    ax.plot(profile, linewidth=2, color='r', marker='o', linestyle='dashed')
    ax.set_title('Profile of ' + name)
    ax.set_xlabel('Hours [h]')
    if 'mass' in name:
        ax.set_ylabel('mass [KG/H]', fontsize=12)
    elif 'temp' in name:
        ax.set_ylabel('temperature [°]', fontsize=12)
    else:
        ax.set_ylabel('power [KW]', fontsize=12)

    ax.set_xlim(xmin=0)
    ax.set_ylim(ymin=0, ymax=max(profile)*1.2)
    plt.grid()

    #plt.show()
    plt.savefig(plot_output)
    plt.close()


def plot_double(csv_file, comp_name1, comp_name2):
    plot_output = os.path.join(opt_output_path, 'plot', 'profile of ' +
                               comp_name1)
    df = pd.read_csv(csv_file)
    data1 = df[df['var'].str.contains(comp_name1 + '_' + comp_name2 + '_temp')]
    data1 = data1.reset_index(drop=True)
    profile_temp = data1['value']
    data2 = df[df['var'].str.contains(comp_name2 + '_' + comp_name1 + '_temp')]
    data2 = data2.reset_index(drop=True)
    profile_return_temp = data2['value']
    data3 = df[(df['var'].str.contains('input_')) & (df['var'].str.contains(
        comp_name1))]
    data3 = data3.reset_index(drop=True)
    profile_inputpower = data3['value']
    data4 = df[(df['var'].str.contains('output_')) & (df['var'].str.contains(
        comp_name1))]
    data4 = data4.reset_index(drop=True)
    profile_outputpower = data4['value']
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(profile_inputpower, '-', label='input')
    ax.plot(profile_outputpower, '-', label='output')
    ax2 = ax.twinx()
    ax2.plot(profile_temp, '-r', label='temp')
    ax2.plot(profile_return_temp, '-g', label='return_temp')
    ax.legend(loc='center left', bbox_to_anchor=(0, 1.1), ncol=1)
    ax.grid()
    ax.set_xlabel("Time (h)")
    ax.set_ylabel(r"power[KW]")
    ax2.set_ylabel(r"Temperature ($^\circ$C)")
    ax.set_xlim(xmax=len(profile_temp)*1.2)
    ax2.legend(loc='upper right', bbox_to_anchor=(1.05, 1.18), ncol=1)
    plt.savefig(plot_output)


def get_short_profiles(start_time, time_step, csv_file):
    def combine_items(ori_list):
        new_list = []
        for nr_1 in range(len(ori_list)):
            for nr_2 in range(len(ori_list)):
                if nr_2 != nr_1:
                    new_list.append(ori_list[nr_1] + '_' + ori_list[nr_2])
        return new_list

    elec_list = combine_items(elec_comp_list)
    heat_list = combine_items(heat_comp_list)

    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)

    short_elec_df = pd.DataFrame()
    short_heat_df = pd.DataFrame()
    for element in elements_dict:
        if len(elements_dict[element]) == 1:
            pass
        else:
            if sum(elements_dict[element][
                   start_time: start_time + time_step]) == 0:
                pass
            else:
                if element in elec_list:
                    short_elec_df.insert(0, element,
                                         elements_dict[element][
                                         start_time: start_time + time_step])
                elif element in heat_list:
                    short_heat_df.insert(0, element,
                                         elements_dict[element][
                                         start_time: start_time + time_step])

    return short_elec_df, short_heat_df


def plot_short_time(start_time, time_step, csv_file, demand_heat, demand_elec):
    """Plot only short time like one day in a graphic"""
    elec_df, heat_df = get_short_profiles(start_time, time_step, csv_file)
    # print(elec_df)
    # print(heat_df)

    demand_heat = demand_heat[start_time: start_time + time_step]
    demand_elec = demand_elec[start_time: start_time + time_step]

    # plot for heat balance
    plot_step_profile(energy_type='heat', demand=demand_heat, profile=heat_df,
                      time_step=time_step)

    # plot for electricity balance
    plot_step_profile(energy_type='elec', demand=demand_elec, profile=elec_df,
                      time_step=time_step)


def plot_step_profile(energy_type, demand, profile, time_step):
    fig = plt.figure(figsize=(6, 5.5))
    ax = fig.add_subplot(1, 1, 1)

    time_steps = range(time_step)
    accumulate_series = pd.Series([0] * time_step)
    x_axis = np.linspace(0, time_step - 1, time_step)

    if energy_type == 'heat':
        sink_tuple = heat_sink_tuple
    elif energy_type == 'elec':
        sink_tuple = elec_sink_tuple
    else:
        sink_tuple = None

    order_heat = 1.5
    for device in profile.columns:
        if not device.endswith(sink_tuple):
            accumulate_series += profile[device]
            ax.step(time_steps, accumulate_series, where="post",
                    label=device, linewidth=2, zorder=order_heat)
            ax.fill_between(x_axis, accumulate_series,
                            step="post", zorder=order_heat)
            order_heat -= 0.1
    for device in profile.columns:
        if device.endswith(sink_tuple):
            last_series_heat = copy.deepcopy(accumulate_series)
            accumulate_series -= profile[device]
            ax.step(time_steps, accumulate_series, where="post",
                    linewidth=0.1, zorder=1.5)
            ax.fill_between(x_axis, last_series_heat, accumulate_series,
                            label=device, step="post", zorder=1.6,
                            hatch='///', alpha=0)
            order_heat -= 0.1
    ax.step(time_steps, demand, where="post", label='Bedarf', linestyle='--',
            linewidth=2, zorder=1.5)

    ax.set_ylabel('Leistung in kW')
    ax.set_xlim(0, 23)
    ax.set_ylim(0, None)
    ax.set_xlabel('Stunde')

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='upper right')
    ax.grid(axis="y", alpha=0.6)
    ax.set_axisbelow(True)
    fig.suptitle(t='hourly profile', fontsize=18)
    plt.show()

    # plot_path = os.path.join(OUTPUTS_PATH, str(datetime.datetime.now(
    #     ).strftime('%Y-%m-%d_%H_%M_%S_')) + day + '.png')

    # plot_path = os.path.join(OUTPUTS_PATH, name + day + '.png')
    # plt.savefig(plot_path)
    # plt.close()


def find_element(output_df):
    """find all elements in dataframe, the variables with same name but
    different time step would be stored in a list"""
    output_df['var_pre'] = output_df['var'].map(lambda x: x.split('[')[0])
    all_elements = output_df['var_pre'].tolist()
    element_list = list(set(all_elements))  # delete duplicate elements

    elements_dict = {}
    for element in element_list:
        element_df = output_df.loc[output_df['var_pre'] == element]
        values = element_df['value'].tolist()
        elements_dict[element] = values

    return elements_dict


if __name__ == '__main__':
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    opt_output_path = os.path.join(base_path, 'data', 'opt_output')
    # opt_output = os.path.join(opt_output_path, 'denmark_energy_hub_result.csv')
    opt_output = os.path.join(opt_output_path, 'project_1_result.csv')
    plot_output = os.path.join(opt_output_path, 'plot')

    demand_input = os.path.join(base_path, 'data', 'denmark_energy_hub',
                                'energyprofile(kwh).csv')
    demand_df = pd.read_csv(demand_input)
    commercial_heat = demand_df['commercial heat'].astype('float64').values
    resident_heat = demand_df['residential heat'].astype('float64').values
    total_heat = commercial_heat + resident_heat
    total_elec = demand_df['total electricity'].astype('float64').values

    # plot_all(opt_output)
    plot_short_time(start_time=0, time_step=24, csv_file=opt_output,
                    demand_heat=total_heat, demand_elec=total_elec)
