"""
Tool to analyse the output csv from optimization
"""

import os
import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Attention! The elec_list and heat_list use the name from topology
# matrix, for different scenario the name for each component may change.
# Need to check for every scenario or fix the component name in topology.
elec_comp_list = ['heat_pump', 'pv', 'bat', 'e_grid', 'e_boi', 'e_cns',
                  'chp']
heat_comp_list = ['heat_pump', 'therm_cns', 'water_tes', 'solar_coll',
                  'boi', 'e_boi', 'chp']
elec_senk_list = ['heat_pump', 'bat', 'e_grid', 'e_boi', 'e_cns']
heat_senk_list = ['water_tes', 'therm_cns']


def plot_all(csv_file):
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    size_dict = {}
    for element in elements_dict:
        if len(elements_dict[element]) == 1:
            if 'size' in element and not np.isnan(elements_dict[element][0]):
                size_dict[element] = elements_dict[element][0]
        else:
            plot_single(element, elements_dict[element])
            # print(element)
            # if element == 'heat_pump_water_tes':
            #     plot_single(element, elements_dict[element])
            pass


def plot_single(name, profile):
    plt.figure()
    plt.plot(profile)
    plt.title('Profile of ' + name)
    plt.ylabel('kW')
    plt.xlabel('Hours [h]')
    plt.ylim(ymin=0)
    plt.xlim(xmin=0)
    plt.grid()

    plt.show()
    plt.close()


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
    print(elec_df)
    print(heat_df)

    demand_heat = demand_heat[start_time: start_time + time_step]
    demand_elec = demand_elec[start_time: start_time + time_step]

    ###########################################################################
    # plot for heat balance
    ###########################################################################
    plot_step_profile(energy_type='heat', demand=demand_heat, profile=heat_df,
                      time_step=time_step)
    # order_heat = 1.5
    # for device in heat_df.columns:
    #     if heat_df[device].sum() != 0:
    #         if device != "TES":
    #             accumulate_series_heat += heat_df[device]
    #             ax_heat.step(time_steps, accumulate_series_heat, where="post",
    #                          label=device, linewidth=2, zorder=order_heat)
    #             ax_heat.fill_between(x_axis, accumulate_series_heat,
    #                                  step="post", zorder=order_heat)
    #             order_heat -= 0.1
    #         else:
    #             last_series_heat = copy.deepcopy(accumulate_series_heat)
    #             accumulate_series_heat -= heat_df[device]
    #             ax_heat.step(time_steps, accumulate_series_heat, where="post",
    #                          linestyle='--', linewidth=2,
    #                          zorder=1.5)
    #             ax_heat.fill_between(x_axis, last_series_heat,
    #                                  accumulate_series_heat,
    #                                  label=device,
    #                                  step="post", zorder=1.6,
    #                                  hatch='///', alpha=0)
    #             order_heat -= 0.1
    # ax_heat.step(time_steps, demand_heat, where="post",
    #              label='Bedarf', linestyle='--', linewidth=2,
    #              zorder=1.5)
    #
    # ax_heat.set_ylabel('Leistung in kW')
    # ax_heat.set_xlim(0, 23)
    # ax_heat.set_ylim(0, None)
    # ax_heat.set_xlabel('Stunde')
    #
    # handles, labels = ax_heat.get_legend_handles_labels()
    # ax_heat.legend(handles[::-1], labels[::-1], loc='upper right')
    # ax_heat.grid(axis="y", alpha=0.6)
    # ax_heat.set_axisbelow(True)
    #
    # ###########################################################################
    # # plot for electricity balance
    # ###########################################################################
    plot_step_profile(energy_type='elec', demand=demand_elec, profile=elec_df,
                      time_step=time_step)
    # order_elec = 1.5
    # for device in elec_df.columns:
    #     if elec_df[device].sum() != 0 or device == "BAT":
    #         if device not in ["BAT", "HP", "EB", "to grid"]:
    #             accumulate_series_elec += elec_df[device]
    #             # ax_elec.step(time_steps, accumulate_series_elec, where="post",
    #             #              label=device, linewidth=2, zorder=order_elec)
    #             ax_elec.fill_between(x_axis, accumulate_series_elec,
    #                                  step="post",
    #                                  label=device, zorder=order_elec)
    #             order_elec -= 0.1
    #         elif device == 'BAT':
    #             last_series_elec = copy.deepcopy(accumulate_series_elec)
    #             accumulate_series_elec -= elec_df[device]
    #             # ax_elec.step(time_steps, accumulate_series_elec, where="post",
    #             #              linestyle='--', linewidth=2,
    #             #              zorder=1.5)
    #             ax_elec.fill_between(x_axis, last_series_elec,
    #                                  accumulate_series_elec,
    #                                  label=device,
    #                                  step="post", zorder=1.6,
    #                                  hatch='///', alpha=0)
    #             order_heat -= 0.1
    #         elif device == 'HP':
    #             last_series_elec = copy.deepcopy(accumulate_series_elec)
    #             accumulate_series_elec += elec_df[device]
    #             # ax_elec.step(time_steps, accumulate_series_elec, where="post",
    #             #              linewidth=2,
    #             #              zorder=1.5)
    #             # ax_elec.step(time_steps, accumulate_series_elec, where="post",
    #             #              linestyle='--', linewidth=2,
    #             #              zorder=1.5)
    #             ax_elec.fill_between(x_axis, last_series_elec,
    #                                  accumulate_series_elec,
    #                                  label=device,
    #                                  step="post", zorder=1.6,
    #                                  hatch='||', alpha=0)
    #             order_heat -= 0.1
    #         elif device == 'EB':
    #             last_series_elec = copy.deepcopy(accumulate_series_elec)
    #             accumulate_series_elec += elec_df[device]
    #             # ax_elec.step(time_steps, accumulate_series_elec, where="post",
    #             #              linestyle='--', linewidth=2,
    #             #              zorder=1.5)
    #             # ax_elec.step(time_steps, accumulate_series_elec, where="post",
    #             #              linewidth=2,
    #             #              zorder=1.5)
    #             ax_elec.fill_between(x_axis, last_series_elec,
    #                                  accumulate_series_elec,
    #                                  label=device,
    #                                  step="post", zorder=1.6,
    #                                  hatch='+++', alpha=0)
    #             order_heat -= 0.1
    #         elif device == 'to grid':
    #             last_series_elec = copy.deepcopy(accumulate_series_elec)
    #             accumulate_series_elec += elec_df[device]
    #             # ax_elec.step(time_steps, accumulate_series_elec, where="post",
    #             #              linestyle='--', linewidth=2,
    #             #              zorder=1.5)
    #             # ax_elec.step(time_steps, accumulate_series_elec, where="post",
    #             #              linewidth=2,
    #             #              zorder=1.5)
    #             ax_elec.fill_between(x_axis, last_series_elec,
    #                                  accumulate_series_elec,
    #                                  label=device,
    #                                  step="post", zorder=1.6,
    #                                  hatch='\\\\', alpha=0)
    #             order_heat -= 0.1
    #         # else:
    #         #     accumulate_series_elec -= time_series_elec[device]
    #         #     ax_elec.step(time_steps, accumulate_series_elec, where="post",
    #         #                  label=device, linestyle='--', linewidth=2,
    #         #                  zorder=1.5)
    #         #     order_elec -= 0.1
    #
    # ax_elec.step(time_steps, demand_elec, where="post",
    #              label='Bedarf', linestyle='--', linewidth=2,
    #              zorder=1.5)
    #
    # ax_elec.set_ylabel('Leistung in kW')
    # ax_elec.set_xlim(0, 23)
    # ax_elec.set_ylim(0, None)
    # ax_elec.set_xlabel('Stunde')
    #
    # handles, labels = ax_elec.get_legend_handles_labels()
    # ax_elec.legend(handles[::-1], labels[::-1], loc='upper right')
    # ax_elec.grid(axis="y", alpha=0.6)
    # ax_elec.set_axisbelow(True)
    #
    # fig.suptitle(t='hourly profile', fontsize=18)
    # plt.show()
    # plot_path = os.path.join(OUTPUTS_PATH, str(datetime.datetime.now(
    #     ).strftime('%Y-%m-%d_%H_%M_%S_')) + day + '.png')

    # plot_path = os.path.join(OUTPUTS_PATH, name + day + '.png')
    # plt.savefig(plot_path)
    # plt.close()


def plot_step_profile(energy_type, demand, profile, time_step):
    fig = plt.figure(figsize=(6, 5.5))
    ax = fig.add_subplot(1, 1, 1)

    time_steps = range(time_step)
    accumulate_series = pd.Series([0] * time_step)
    x_axis = np.linspace(0, time_step - 1, time_step)

    if energy_type == 'heat':
        pass
    elif energy_type == 'elec':
        pass

    order_heat = 1.5
    for device in profile.columns:
        if device != "TES":
            accumulate_series += profile[device]
            ax.step(time_steps, accumulate_series, where="post",
                         label=device, linewidth=2, zorder=order_heat)
            ax.fill_between(x_axis, accumulate_series,
                                 step="post", zorder=order_heat)
            order_heat -= 0.1
        else:
            last_series_heat = copy.deepcopy(accumulate_series)
            accumulate_series -= profile[device]
            ax.step(time_steps, accumulate_series, where="post",
                         linestyle='--', linewidth=2,
                         zorder=1.5)
            ax.fill_between(x_axis, last_series_heat,
                                 accumulate_series,
                                 label=device,
                                 step="post", zorder=1.6,
                                 hatch='///', alpha=0)
            order_heat -= 0.1
    ax.step(time_steps, demand, where="post",
                 label='Bedarf', linestyle='--', linewidth=2,
                 zorder=1.5)

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
