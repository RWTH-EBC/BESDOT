"""
Tool to analyse the output csv from optimization
"""

import os
import re
import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import ImageColor
import matplotlib.patches as mpatches

# Attention! The elec_list and heat_list use the name from topology
# matrix, for different scenario the name for each component may change.
# Need to check for every scenario or fix the component name in topology.
elec_comp_list = ['heat_pump', 'pv', 'bat', 'e_grid', 'e_boi', 'e_cns',
                  'chp']
heat_comp_list = ['heat_pump', 'therm_cns', 'water_tes', 'solar_coll',
                  'boi', 'e_boi', 'chp']
elec_sink_tuple = ('heat_pump', 'bat', 'e_grid', 'e_boi')
heat_sink_tuple = 'water_tes'
#plt.rcParams['axes.unicode_minus']=False

# base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# opt_output_path = os.path.join(base_path, 'data', 'opt_output')


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


def find_size(csv_file):
    """
    Search for the results of each component in csv file.
    """
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    size_dict = {}
    for element in elements_dict:
        if len(elements_dict[element]) == 1:
            if 'size' in element and not np.isnan(elements_dict[element][0]):
                size_dict[element] = elements_dict[element][0]
                print('The size of', element, 'is', size_dict[element])
            if 'volume' in element and not np.isnan(
                    elements_dict[element][0]):
                size_dict[element] = elements_dict[element][0]
                print('The volume of', element, 'is', size_dict[element])


def sum_flow(csv_file, flow_name):
    """
    Calculate the sum of a specific energy flow in result file.
    """
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    flow_list = elements_dict[flow_name]
    print(sum(flow_list))


def find_max_timestep(csv_file, profile_name):
    """Search the maximal value of a profile and return the timestep of the
    maximal value. This function could be used to analysis the situation,
    how the peak demand is filled.
    Using find_element().keys() to find the name of the wanted profile"""
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    profile = elements_dict[profile_name]
    max_value = max(profile)
    index_max = profile.index(max(profile))

    return max_value, index_max


def save_timeseries(csv_file, name=''):
    """Take the time series from output file and save them as an individual
    csv file, to reduce the analysis time cost."""
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    new_df = pd.DataFrame()

    for item in elements_dict.keys():
        if len(elements_dict[item]) > 1:
            new_df = pd.DataFrame(index=range(len(elements_dict[item])))
            break

    for item in elements_dict.keys():
        if len(elements_dict[item]) > 1:
            if 'status' in item:  # quick fix for status in chp, need to
                # be fixed in the future
                # new_df[item] = elements_dict[item]
                pass
            elif 'building_connect' in item:
                # new_df[item] = elements_dict[item]
                pass
            elif 'energy_edge' in item:
                # new_df[item] = elements_dict[item]
                pass
                # print('---')
                # print(item)
                # print(elements_dict[item])
            elif 'energy_on_edges' in item:
                # print('+++')
                # print(item)
                # print(elements_dict[item])
                pass
                # new_df[item] = elements_dict[item]
            else:
                new_df[item] = elements_dict[item]


    # print(new_df)
    output_path = os.path.split(csv_file)
    timeseries_path = os.path.join(output_path[0], name + '_timeseries.xlsx')
    new_df.to_excel(timeseries_path)


def save_non_time_series(csv_file, name=''):
    """Take the non time series from output file and save them as an individual
    csv file, to reduce the analysis time cost."""
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    new_df = pd.DataFrame()

    for item in elements_dict.keys():
        if len(elements_dict[item]) == 1:
            new_df[item] = elements_dict[item]

    new_df = new_df.T

    # print(new_df)
    output_path = os.path.split(csv_file)
    non_timeseries_path = os.path.join(output_path[0],
                                       name + '_non_timeseries.xlsx')
    new_df.to_excel(non_timeseries_path)


def save_all_data_network(input_csv, output_prefix, time_index):
    # Load the data from the CSV file
    data = pd.read_csv(input_csv)

    # Extract the prefix of each state (excluding the time label)
    data['prefix'] = data['var'].str.extract(r'(.*)\[')

    # Count the occurrences of each prefix
    prefix_counts = data['prefix'].value_counts()

    # Filter data based on the count of states
    data_timestep_states = data[data['prefix'].isin(prefix_counts[
                                                        prefix_counts ==
                                                        time_index].index)]
    data_single_state = data[data['prefix'].isin(prefix_counts[prefix_counts
                                                               == 1].index)]
    # data_multi_states = data[data['prefix'].isin(
    #     prefix_counts[(prefix_counts > 1) & (prefix_counts != time_index)].index)]

    connect_data = data[data['var'].str.contains('building_connect', na=False)]

    edge_data = data[data['var'].str.contains('energy_edge', na=False)]
    edge_data['time_index'] = edge_data['var'].str.extract(
        r'.*\,(\d+)\]$').astype(int)
    edge_data['new_var'] = edge_data.apply(
        lambda row: re.sub(r',\d+\]$', ']', row['var']), axis=1)
    edge_data = edge_data.pivot(index='new_var', columns='time_index', values='value')
    edge_data = edge_data.groupby(edge_data.index).first()

    on_edge_data = data[data['var'].str.contains('energy_on_edge', na=False)]
    on_edge_data['time_index'] = on_edge_data['var'].str.extract(
        r'.*\,(\d+)\]$').astype(int)
    on_edge_data['new_var'] = on_edge_data.apply(
        lambda row: re.sub(r',\d+\]$', ']', row['var']), axis=1)
    on_edge_data = on_edge_data.pivot(index='new_var', columns='time_index',
                                values='value')
    on_edge_data = on_edge_data.groupby(on_edge_data.index).first()

    # Save data to Excel files
    output_path = os.path.split(input_csv)
    data_timestep_states.drop(columns='prefix').to_excel(os.path.join(output_path[0],
        f"{output_prefix}_timestep_states.xlsx"), index=False)
    connect_data.drop(columns='prefix').to_excel(os.path.join(
        output_path[0], f"{output_prefix}_connect_data.xlsx"), index=False)
    edge_data.to_excel(os.path.join(
        output_path[0], f"{output_prefix}_edge_data.xlsx"), index=True)
    on_edge_data.to_excel(os.path.join(
        output_path[0], f"{output_prefix}_on_edge_data.xlsx"), index=True)
    data_single_state.drop(columns='prefix').to_excel(os.path.join(
        output_path[0], f"{output_prefix}_single_state.xlsx"), index=False)

    print("Data processing completed and saved to Excel files.")


# def save_all_data_network(input_csv, output_prefix, max_time_index):
#     # Load the data from the CSV file
#     data = pd.read_csv(input_csv)
#
#     # Extract the time index from the 'var' column
#     data['time_index'] = data['var'].str.extract(r'.*\[(\d+)\]$')
#     # Extract the prefix of each state (excluding the time label)
#     data['prefix'] = data['var'].str.extract(r'(.*)\[')
#
#     # Drop rows with NaN in 'time_index' column
#     data = data.dropna(subset=['time_index'])
#
#     # Convert 'time_index' column to integer
#     data['time_index'] = data['time_index'].astype(int)
#
#     # Pivot the data to wide format
#     wide_data = data.pivot(index='prefix', columns='time_index', values='value')
#
#     # Filter data based on the count of states
#     data_24_states = wide_data[wide_data.count(axis=1) == max_time_index]
#     data_multi_states = wide_data[(wide_data.count(axis=1) > 1) & (
#                 wide_data.count(axis=1) != max_time_index)]
#     data_single_state = wide_data[wide_data.count(axis=1) == 1]
#
#     # Save to Excel (or further processing)
#     with pd.ExcelWriter(output_prefix + '_output.xlsx') as writer:
#         data_24_states.to_excel(writer, sheet_name='24_states')
#         data_multi_states.to_excel(writer, sheet_name='multi_states')
#         data_single_state.to_excel(writer, sheet_name='single_state')


def plot_all(csv_file, time_interval, save_path=None):
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
            if sum(elements_dict[element]) > 0.001 or sum(elements_dict[
                                                              element]) < 0.001:
                plot_single(element,
                            elements_dict[element][time_interval[0]:
                                                   time_interval[1]],
                            save_path)


def plot_single(name, profile, plot_path=None):
    """
    name: the name for a variable in optimization model and results.
    profile: already taken fom the result dictionary and the time steps are
    taken into account as well.
    plot_path: the folder address for all plots, it should be the same folder
    for model and optimization results.
    """
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot(profile, linewidth=2, color='r', linestyle='-')
    ax.set_title('Profile of ' + name)
    ax.set_xlabel('Hours [h]')
    if 'mass' in name:
        ax.set_ylabel('Mass [KG/H]', fontsize=12)
    elif 'temp' in name:
        ax.set_ylabel('Temperature [°C]', fontsize=12)
    elif 'pmv' in name:
        ax.set_ylabel('PMV', fontsize=12)
    else:
        ax.set_ylabel('Power [KW]', fontsize=12)

    if 'pmv' in name:
        ax.set_xlim(xmin=0)
        ax.set_ylim(ymin=-3, ymax=3)
    else:
        ax.set_xlim(xmin=0)
        ax.set_ylim(ymin=0, ymax=max(profile) * 1.2)
    plt.grid()

    if plot_path is not None:
        plt.savefig(os.path.join(plot_path, name+'.png'))
    else:
        plt.show()
    plt.close()


def plot_double_24h(csv_file, comp_name1, comp_name2):
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
    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.plot(profile_inputpower, '-', label='input')
    ax.plot(profile_outputpower, '-', label='output')
    ax2 = ax.twinx()
    ax2.plot(profile_temp, '-r', label=comp_name1 + '_' + comp_name2 + '_temp')
    ax2.plot(profile_return_temp, '-g', label=comp_name2 + '_' + comp_name1 +
                                              '_temp')
    ax.legend(loc='center left', bbox_to_anchor=(0, 1.07), ncol=1)
    ax.grid()
    ax.set_xlabel("Time (h)")
    ax.set_title('Profile of ' + comp_name1, fontsize=9)
    ax.set_ylabel(r"Power (KW)")
    ax2.set_ylabel(r"Temperature ($^\circ$C)")
    ax.set_xlim(xmax=len(profile_temp))
    ax2.legend(loc='upper right', bbox_to_anchor=(1.1, 1.15), ncol=1)
    plt.savefig(plot_output)


def plot_double(csv_file, comp_name1, comp_name2, time_step, inputenergy,
                outputenergy):
    #plot_output = os.path.join(opt_output_path, 'plot', 'profile of ' +
    #                           comp_name1)
    df = pd.read_csv(csv_file)
    #data1 = df[df['var'].str.contains(comp_name1 + '_' + comp_name2 + '_temp')]
    #data1 = data1.reset_index(drop=True)
    #profile_temp = data1['value']
    profile_temp_original, profile_return_temp_original, \
    profile_inputpower_original, profile_outputpower_original = \
        get_info_for_figu(csv_file, comp_name1, comp_name2, time_step,
                          inputenergy, outputenergy)
    for i in range(1, len(profile_temp_original)+1):
        if i < len(profile_temp_original)+1:
            plot_output = os.path.join(opt_output_path, 'plot', 'profile of ' +
                                       comp_name1 + ' day ' + str(i))
            profile_temp = profile_temp_original[i-1]
            profile_return_temp = profile_return_temp_original[i-1]
            profile_inputpower = profile_inputpower_original[i-1]
            profile_outputpower = profile_outputpower_original[i-1]
            fig = plt.figure(figsize=(6.5, 5.5))
            ax = fig.add_subplot(111)
            ax.plot(profile_inputpower, '-', label='input')
            ax.plot(profile_outputpower, '--', label='output')
            ax2 = ax.twinx()
            ax2.plot(profile_temp, '-r',
                     label=comp_name1 + '_' + comp_name2 + '_temp')
            ax2.plot(profile_return_temp, '-g',
                     label=comp_name2 + '_' + comp_name1 +
                           '_temp')
            ax.legend(loc='center left', bbox_to_anchor=(0, 1.07), ncol=1)
            ax.grid()
            ax.set_xlabel("Time (h)")
            ax.set_title('Profile of ' + comp_name1 + ' day ' + str(i),
                         fontsize=9)
            ax.set_ylabel(r"Power (KW)")
            ax2.set_ylabel(r"Temperature ($^\circ$C)")
            ax.set_xlim(xmax=24)
            ax2.legend(loc='upper right', bbox_to_anchor=(1.1, 1.15), ncol=1)
            plt.savefig(plot_output)
            i = i + 1


def get_info_for_figu(csv_file, comp_name1, comp_name2, time_step,
                             inputenergy, outputenergy):
    df = pd.read_csv(csv_file)
    name1 = comp_name1 + '_' + comp_name2 + '_temp[1]'
    name2 = comp_name2 + '_' + comp_name1 + '_temp[1]'
    name3 = 'input_' + inputenergy + '_' + comp_name1 + '[1]'
    name4 = 'output_' + outputenergy + '_' + comp_name1 + '[1]'
    part = int(8760/time_step)
    temp = []
    return_temp = []
    input_power = []
    output_power = []
    pa = []
    pa_co = 1
    for i in range(1, 313):
        if pa_co != part:
            pa.append(df["value"][df[df["var"] == str(name1[:-2] + str(i)+"]")].
                      index].to_list()[0])
            pa_co += 1
        else:
            pa_co = 1
            pa.append(df["value"][df[df["var"] == str(name1[:-2] + str(i)+"]")].
                      index].to_list()[0])
            temp.append(pa)
            pa = []
    for i in range(1, 313):
        if pa_co != part:
            pa.append(
                df["value"][df[df["var"] == str(name2[:-2] + str(i) + "]")].
                index].to_list()[0])
            pa_co += 1
        else:
            pa_co = 1
            pa.append(
                df["value"][df[df["var"] == str(name2[:-2] + str(i) + "]")].
                index].to_list()[0])
            return_temp.append(pa)
            pa = []
    for i in range(1, 313):
        if pa_co != part:
            pa.append(
                df["value"][df[df["var"] == str(name3[:-2] + str(i) + "]")].
                index].to_list()[0])
            pa_co += 1
        else:
            pa_co = 1
            pa.append(
                df["value"][df[df["var"] == str(name3[:-2] + str(i) + "]")].
                index].to_list()[0])
            input_power.append(pa)
            pa = []
    for i in range(1, 313):
        if pa_co != part:
            pa.append(
                df["value"][df[df["var"] == str(name4[:-2] + str(i) + "]")].
                index].to_list()[0])
            pa_co += 1
        else:
            pa_co = 1
            pa.append(
                df["value"][df[df["var"] == str(name4[:-2] + str(i) + "]")].
                index].to_list()[0])
            output_power.append(pa)
            pa = []
    return temp, return_temp, input_power, output_power


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


def plot_temp(name, profile):
    plot_output = os.path.join(opt_output_path, 'plot', 'Profile of ' + name)
    fig, ax = plt.subplots(figsize=(14, 14))
    #ax = fig.add_subplot(111)
    ax.plot(profile, linewidth=2, color='r', marker='o', linestyle='dashed')
    ax.set_title('Profile of ' + name, fontsize=24)
    ax.set_xlabel('Hours [h]', fontsize=24)
    if 'mass' in name:
        ax.set_ylabel('mass [KG/H]', fontsize=12)
    elif 'temp' in name:
        ax.set_ylabel('temperature [°]', fontsize=24)
    else:
        ax.set_ylabel('power [KW]', fontsize=12)

    ax.set_xlim(xmin=0)
    ax.set_ylim(ymin=0, ymax=max(profile)*1.2)

    plt.xticks([0, 2161, 4345, 6553, 8017],
               [r'$1.Jar.$', r'$1.Apr.$', r'$1.Jul.$', r'$1.Oct.$',
                r'$1.Dec.$'], fontsize=29)
    plt.yticks(fontsize=29)

    plt.grid()

    #plt.show()
    plt.savefig(plot_output)
    plt.close()


def create_stacked_bar_chart(x, stacked_data1, label1, stacked_data2,
                             label2,  x_label, y_label, title=None,
                             start_index=None,
                             end_index=None):
    """
    Create a chart with stacked bar plots

    Args:
    x (ndarray): x-axis data
    stacked_data1 (ndarray): First set of stacked data
    stacked_data2 (ndarray): Second set of stacked data
    """
    # Apply slicing to data1 and data2 if start_index and end_index are specified
    if start_index is not None and end_index is not None:
        stacked_data1 = stacked_data1[start_index:end_index]
        stacked_data2 = stacked_data2[start_index:end_index]
        x = x[start_index:end_index]

    # Create stacked bar plot
    plt.bar(x, stacked_data1, label=label1)
    plt.bar(x, stacked_data2, bottom=stacked_data1, label=label2)

    # Add legend
    plt.legend()

    # Add axis labels
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    # Show the chart
    plt.show()


# def create_stacked_bar_line_chart(x, stacked_data, stacked_label, line_data,
#                                   line_label, x_label, y_label, title=None,
#                                   start_index=None, end_index=None):
#     """
#     Create a chart with stacked bar and line plots
#
#     Args:
#     x (ndarray): x-axis data
#     stacked_data (list of ndarrays): List of stacked data, each array represents
#      a column of data line_data (ndarray): Line plot data, representing the
#      sum of stacked data
#     """
#     num_stacked = len(stacked_data)  # Number of stacked data
#
#     # Apply slicing to data1 and data2 if start_index and end_index are specified
#     if start_index is not None and end_index is not None:
#         stacked_data = [data[start_index:end_index] for data in stacked_data]
#         line_data = line_data[start_index:end_index]
#         x = x[start_index:end_index]
#
#     # Create stacked bar plot
#     bottoms = np.zeros(len(x))  # Initial bottom heights
#     for i in range(num_stacked):
#         if sum(stacked_data[i]) > 0.001:
#             plt.bar(x, stacked_data[i], bottom=bottoms, label=stacked_label[i])
#             bottoms += stacked_data[i]
#
#     # Create line plot
#     plt.plot(x, line_data, color='red', linestyle='-', label=line_label)
#
#     # Add legend
#     plt.legend()
#
#     # Calculate y-axis limits
#     y_min = min(0, min(bottoms), min(line_data))
#     y_max = max(max(bottoms), max(line_data)*1.1)
#
#     plt.ylim(y_min, y_max)
#
#     # Add axis labels
#     plt.xlabel(x_label)
#     plt.ylabel(y_label)
#     plt.title(title)
#
#     # Show the chart
#     plt.show()

def create_stacked_bar_line_chart(x, stacked_data, stacked_label, line_data,
                                  line_label, x_label, y_label, title=None,
                                  start_index=None, end_index=None, step_length=1):
    """
    Create a chart with stacked bar and line plots

    Args:
    x (ndarray): x-axis data
    stacked_data (list of ndarrays): List of stacked data, each array represents
     a column of data line_data (ndarray): Line plot data, representing the
     sum of stacked data
    """
    num_stacked = len(stacked_data)  # Number of stacked data

    # Apply slicing to data1 and data2 if start_index and end_index are specified
    if start_index is not None and end_index is not None:
        stacked_data = [data[start_index:end_index] for data in stacked_data]
        line_data = line_data[start_index:end_index]
        x = x[start_index:end_index]

    assert len(x) % step_length == 0
    assert len(line_data) % step_length == 0
    assert all(len(arr) % step_length == 0 for arr in stacked_data)

    # x = np.array(x).reshape(-1, step_length).tolist()
    x = np.array(x).reshape(-1, step_length).min(axis=1).tolist()
    line_data = np.array(line_data).reshape(-1, step_length).sum(
        axis=1).tolist()

    for i in range(len(stacked_data)):
        stacked_data[i] = np.array(stacked_data[i]).reshape(-1,
                                                            step_length).sum(
            axis=1).tolist()

    # Create stacked bar plot
    bar_width = (max(x) - min(x)) / len(x)  # Calculate the width of the bar
    bottoms = np.zeros(len(x))  # Initial bottom heights
    for i in range(num_stacked):
        if sum(stacked_data[i]) > 0.001:
            plt.bar(x, stacked_data[i], bottom=bottoms, label=stacked_label[i],
                    width=bar_width)  # set the width parameter
            bottoms += stacked_data[i]

    # Create line plot
    plt.plot(x, line_data, color='red', linestyle='-', label=line_label)

    # Add legend
    plt.legend()

    # Calculate y-axis limits
    y_min = min(0, min(bottoms), min(line_data))
    y_max = max(max(bottoms), max(line_data)*1.1)

    plt.ylim(y_min, y_max)

    # Add axis labels
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)

    # Show the chart
    plt.show()

# def create_stacked_bar_line_chart(x, stacked_data, stacked_label, line_data,
#                                   line_label, x_label, y_label, title=None,
#                                   start_index=None, end_index=None,
#                                   step_length=1):
#     """
#     Create a chart with stacked bar and line plots
#
#     Args:
#     x (ndarray): x-axis data
#     stacked_data (list of ndarrays): List of stacked data, each array represents
#      a column of data line_data (ndarray): Line plot data, representing the
#      sum of stacked data
#     step_length (int): The length of each step after merging the original data
#     """
#     print('x', x)
#     print('stacked_data', stacked_data)
#     print('line_data', line_data)
#     num_stacked = len(stacked_data)  # Number of stacked data
#
#     # Apply slicing to data1 and data2 if start_index and end_index are specified
#     if start_index is not None and end_index is not None:
#         stacked_data = [data[start_index:end_index] for data in stacked_data]
#         line_data = line_data[start_index:end_index]
#         x = x[start_index:end_index]
#
#     # Merge data based on step_length
#     merged_stacked_data = []
#     merged_line_data = []
#     merged_x = []
#     for i in range(0, len(x), step_length):
#         merged_x.append(x[i])
#         merged_stacked_data.append(
#             [np.sum(data[i:i + step_length]) for data in stacked_data])
#         merged_line_data.append(np.sum(line_data[i:i + step_length]))
#
#     merged_x = merged_x[:len(merged_stacked_data)]
#     print('merged_x', merged_x)
#     print('merged_stacked_data', merged_stacked_data)
#     print('merged_line_data', merged_line_data)
#
#     # Create stacked bar plot
#     bottoms = np.zeros(len(merged_x))  # Initial bottom heights
#     for i in range(num_stacked):
#         if sum(merged_stacked_data[i]) > 0.001:
#             plt.bar(merged_x, merged_stacked_data[i], bottom=bottoms, label=stacked_label[i])
#             bottoms += merged_stacked_data[i]
#
#     # Create line plot
#     plt.plot(merged_x, merged_line_data, color='red', linestyle='-', label=line_label)
#
#     # Add legend
#     plt.legend()
#
#     # Calculate y-axis limits
#     y_min = min(0, min(bottoms), min(merged_line_data))
#     y_max = max(max(bottoms), max(merged_line_data)*1.1)
#
#     plt.ylim(y_min, y_max)
#
#     # Add axis labels
#     plt.xlabel(x_label)
#     plt.ylabel(y_label)
#     plt.title(title)
#
#     # Show the chart
#     plt.show()


def plot_multiple_lines(df, x_column, y_columns):
    """
    Plot multiple lines from DataFrame on the same chart

    Args:
    df (DataFrame): Input DataFrame
    x_column (str): Name of the column for x-axis data
    y_columns (list of str): List of column names for y-axis data
    """
    # Set a color scheme for the lines
    color_scheme = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red',
                    'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray',
                    'tab:olive', 'tab:cyan']

    # Create the chart
    fig, ax = plt.subplots()

    for i, col in enumerate(y_columns):
        x = df[x_column].values
        y = df[col].values

        ax.plot(x, y, color=color_scheme[i % len(color_scheme)], label=col)

    # Add legend
    ax.legend()

    # Set y-axis limits based on the data range
    y_min = df[y_columns].min().min()  # Minimum value from all y-columns
    y_max = df[y_columns].max().max()  # Maximum value from all y-columns

    ax.set_ylim(y_min, y_max)

    # Add axis labels
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    # Show the chart
    plt.show()


def plot_comparison(df, indices, labels=[]):
    fig, ax = plt.subplots()

    width = 0.4
    group_width = len(indices) * 2 * width + 1

    group_colors = sns.color_palette('hls', len(indices))  # 为每个组选择一个颜色
    legend_patches = []

    for group_num, (stack_indices1, stack_indices2) in enumerate(indices):
        stack_data1 = df.loc[stack_indices1].values.flatten()
        stack_data1 = np.nan_to_num(stack_data1, nan=0)  # 将NaN替换为0
        stack_data2 = df.loc[stack_indices2].values.flatten()
        stack_data2 = np.nan_to_num(stack_data2, nan=0)  # 将NaN替换为0

        x1 = np.array([group_num * group_width])
        x2 = np.array([group_num * group_width + width])

        for x, stack_data, stack_indices in [(x1, stack_data1, stack_indices1),
                                             (x2, stack_data2, stack_indices2)]:
            bottom = 0
            for i, data in enumerate(stack_data):
                data = round(data)
                if data != 0:
                    color = sns.light_palette(group_colors[group_num], len(stack_data) + 2, reverse=True, input='rgb')[i + 1]
                    color = sns.set_hls_values(color, l=(i + 1) / (len(stack_data) + 1))  # 调整亮度来增加颜色差别
                    ax.bar(x, data, bottom=bottom, width=width, color=color)
                    rgb_color = tuple(int(255 * x) for x in color[:3])
                    grayscale = 0.2989 * rgb_color[0] + 0.5870 * rgb_color[1] + 0.1140 * rgb_color[2]  # 将颜色转换为灰度
                    text_color = 'white' if grayscale < 128 else 'black'  # 基于灰度决定使用黑色还是白色文字
                    ax.text(x, bottom + data / 2, str(data), ha='center',
                            va='center', color=text_color)
                    bottom += data
                    legend_patches.append(mpatches.Patch(color=color,
                                                         label=stack_indices[
                                                             i]))

        total1 = np.sum(stack_data1)
        total2 = np.sum(stack_data2)
        shorter = min(total1, total2)
        taller = max(total1, total2)
        relative_error = abs(total1 - total2) / shorter * 100
        if relative_error < -0.1:
            diff_bar = x1[0]
            diff_height = shorter + (taller - shorter) / 2
        elif relative_error > 0.1:
            diff_bar = x2[0]
            diff_height = shorter + (taller - shorter) / 2
        else:
            diff_bar = x1[0] + width / 2
            diff_height = shorter + 100
        ax.text(diff_bar, diff_height,
                f'Δ {relative_error:.1f}%', ha='center', va='center')

    ax.set_xticks(np.arange(len(indices)) * group_width + width/2)
    ax.set_xticklabels(labels)
    ax.legend(handles=legend_patches)

    plt.show()


def plot_size(non_timeseries_path):
    non_timeseries_df = pd.read_excel(non_timeseries_path, header=0,
                                      names=['Variable', 'Value'])

    # 过滤带有"grid"的变量
    non_grid_df = non_timeseries_df[
        ~non_timeseries_df['Variable'].str.contains('grid')]

    size_df = non_grid_df[non_grid_df['Variable'].str.contains('size')]

    # 过滤没有数据或值为零的项
    size_df = size_df[size_df['Value'].notna() & (size_df['Value'] != 0)]

    plt.bar(size_df['Variable'], size_df['Value'], label='size')
    plt.legend()

    # 在柱子上显示数值（保留小数点后一位）
    for i, value in enumerate(size_df['Value']):
        plt.text(i, value, f"{value:.1f}", ha='center', va='bottom')

    plt.show()


def plot_network_result(network_result, time="average"):

    def parse_variables(row):
        if 'energy_edges[' in row:
            parts = row.strip('energy_edges[').strip(']').split(',')
            source = 'energy_edges'
        elif 'energy_on_edges[' in row:
            parts = row.strip('energy_on_edges[').strip(']').split(',')
            source = 'energy_on_edges'
        else:
            return None, None, None, None, None, None
        lon_start, lat_start, lon_end, lat_end, time = map(float, parts)
        return lon_start, lat_start, lon_end, lat_end, time, source

    def extract_data_from_pivot(row_name):
        if 'energy_edges' in row_name:
            source = 'energy_edges'
        elif 'energy_on_edges' in row_name:
            source = 'energy_on_edges'
        else:
            return None, None, None, None, None

        parts = row_name.strip('energy_edges[').strip(']').split(',')
        lon_start, lat_start, lon_end, lat_end = map(float, parts)
        return lon_start, lat_start, lon_end, lat_end, source

    def plot_energy_on_edges(dataframe, source, time="average"):
        source_data = dataframe[dataframe['source'] == source]

        # 根据时刻筛选数据或计算平均值
        if time == "average":
            avg_data = source_data.groupby(
                ['lon_start', 'lat_start', 'lon_end', 'lat_end'])[
                'value'].mean().reset_index()
            plot_data = avg_data
        else:
            plot_data = source_data[source_data['time'] == time]

        # Calculate canvas size based on the data's longitude and latitude range
        lon_range = plot_data[['lon_start', 'lon_end']].values.max() - \
                    plot_data[['lon_start', 'lon_end']].values.min()
        lat_range = plot_data[['lat_start', 'lat_end']].values.max() - \
                    plot_data[['lat_start', 'lat_end']].values.min()

        aspect_ratio = lat_range / lon_range
        canvas_width = 12
        canvas_height = canvas_width * aspect_ratio

        fig, ax = plt.subplots(figsize=(canvas_width, canvas_height))

        # 获取数据的最小和最大值以调整颜色映射
        vmin = plot_data['value'].min()
        vmax = plot_data['value'].max()
        norm = plt.Normalize(vmin, vmax)

        # 根据筛选后的数据绘制弧线和箭头
        for index, row in plot_data.iterrows():
            # Check if the opposite direction exists and its value
            opposite_data = plot_data[
                (plot_data['lon_start'] == row['lon_end']) &
                (plot_data['lat_start'] == row['lat_end']) &
                (plot_data['lon_end'] == row['lon_start']) &
                (plot_data['lat_end'] == row['lat_start'])]

            # If the opposite direction doesn't exist or its value is zero, continue drawing
            if opposite_data.empty or opposite_data['value'].iloc[0] == 0:
                # Calculate control points for bezier curve to give it a slight arc
                midpoint = [(row['lon_start'] + row['lon_end']) / 2,
                            (row['lat_start'] + row['lat_end']) / 2]
                control_dx = (row['lat_end'] - row['lat_start']) * 0  # 0
                # could be replaced with other value, 0 is straight line,
                # others like 0.05 for a slight arc.
                control_dy = (row['lon_end'] - row['lon_start']) * 0
                control_point = [midpoint[0] + control_dx,
                                 midpoint[1] - control_dy]

                # Create the bezier curve with the control point
                path = mpatches.PathPatch(mpatches.Path(
                    [(row['lon_start'], row['lat_start']), control_point,
                     (row['lon_end'], row['lat_end'])],
                    [mpatches.Path.MOVETO, mpatches.Path.CURVE3,
                     mpatches.Path.LINETO]),
                                          edgecolor=plt.cm.YlOrRd(
                                              norm(row['value'])), lw=2,
                                          facecolor='none')
                ax.add_patch(path)

        # Adjust the x and y axis limits based on the data's longitude and latitude range
        ax.set_xlim(plot_data[['lon_start', 'lon_end']].values.min(),
                    plot_data[['lon_start', 'lon_end']].values.max())
        ax.set_ylim(plot_data[['lat_start', 'lat_end']].values.min(),
                    plot_data[['lat_start', 'lat_end']].values.max())

        # Adjust margins
        plt.subplots_adjust(left=0.06, right=0.88, top=0.9, bottom=0.1)

        cax = plt.axes([0.90, 0.1, 0.03, 0.8])
        plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap='YlOrRd'),
                     cax=cax, label='Energy Value')

        ax.set_title(
            f'Geographical Visualization of Energy Flow for {source} Data (Time: {time})')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        # ax.grid(True)
        plt.show()

    # pd.set_option('display.max_columns', None)
    data = pd.read_excel(network_result, index_col=0)
    # parsed_data_updated = data['var'].apply(parse_variables)
    # data[['lon_start', 'lat_start', 'lon_end', 'lat_end', 'time', 'source']] = \
    #     pd.DataFrame(parsed_data_updated.tolist(), index=data.index)
    # data = data.drop(columns=['Unnamed: 0', 'var'])
    # data_cleaned = data.dropna(
    #     subset=['lon_start', 'lat_start', 'lon_end', 'lat_end', 'time',
    #             'source'])
    #
    # plot_energy_on_edges(data_cleaned, source="energy_edges", time=time)
    data_list = []
    for index, row in data.iterrows():
        lon_start, lat_start, lon_end, lat_end, source = extract_data_from_pivot(
            index)
        for col, value in row.iteritems():
            if not np.isnan(value):
                data_list.append(
                    [lon_start, lat_start, lon_end, lat_end, col, source,
                     value])

    data_cleaned = pd.DataFrame(data_list,
                                columns=['lon_start', 'lat_start', 'lon_end',
                                         'lat_end', 'time', 'source', 'value'])

    plot_energy_on_edges(data_cleaned, source="energy_edges", time=time)


if __name__ == '__main__':


    # 例子中的数据，实际情况中可以替换成你的数据
    line_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    stacked_data = [np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]),
                    np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])]

    # 设置步长
    step_length = 7

    # 确保数据长度可以被步长整除，如果不能整除，你可能需要裁剪或填充数据
    assert len(line_data) % step_length == 0
    assert all(len(arr) % step_length == 0 for arr in stacked_data)

    line_data = np.array(line_data).reshape(-1, step_length).sum(
        axis=1).tolist()

    for i in range(len(stacked_data)):
        stacked_data[i] = np.array(stacked_data[i]).reshape(-1,
                                                            step_length).sum(
            axis=1).tolist()

    # 输出处理后的数据
    print("line_data:", line_data)
    print("stacked_data:", stacked_data)

