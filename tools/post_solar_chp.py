import os
import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MultipleLocator
from scripts.Environment import Environment

elec_comp_list = ['heat_pump', 'pv', 'bat', 'e_grid', 'e_boi', 'e_cns',
                  'chp']
heat_comp_list = ['heat_pump', 'therm_cns', 'water_tes', 'solar_coll',
                  'boi', 'e_boi', 'chp']
elec_sink_tuple = ('heat_pump', 'bat', 'e_grid', 'e_boi')
heat_sink_tuple = 'water_tes'

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
opt_output_path = os.path.join(base_path, 'data', 'opt_output')


def plot_all(csv_file, time_interval):
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
                                                            time_interval[1]],
                            time_interval)


def plot_single(name, profile, time_interval):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '15'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '18'}
    plot_output = os.path.join(opt_output_path, 'plot', 'Profile of ' + name)
    time_steps = range(time_interval[0], time_interval[1] + 1)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.step(time_steps, profile, where="post", linestyle='-', color='r',
            linewidth=2, zorder=1.5)
    #ax.set_title('Diagram von ' + name, font_titel)
    ax.set_xlabel('Stunde [h]', font_label)
    if 'mass' in name:
        ax.set_ylabel('Massstrom [kg/h]', font_label)
    elif 'temp' in name:
        ax.set_ylabel('Temperaur [°C]', font_label)
    else:
        ax.set_ylabel('leistung [kW]', font_label)

    ax.set_xlim(xmin=0)
    ax.set_ylim(ymin=0, ymax=max(profile) * 1.2)
    plt.grid()

    plt.savefig(plot_output)
    plt.close()

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


def plot_one_line(csv_file, comp, titel, ylabel, n=1.1):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', titel)
    df = pd.read_csv(csv_file)
    data = df[(df['var'].str.contains(comp))]
    data = data.reset_index(drop=True)
    value = data['value']
    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    plt.grid(linestyle='--', which='both')

    ax.plot(value, linewidth=2, color='r', linestyle='-')
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Time (h)", font_label)
    ax.set_ylabel(ylabel, font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(value) * n)
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()
    plt.savefig(plot_output)


def plot_two_lines(csv_file, comp1, comp2, label1, label2, titel, ylabel,
                   n=1.1, legend_pos='best'):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', titel)
    df = pd.read_csv(csv_file)

    data1 = df[(df['var'].str.contains(comp1))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains(comp2))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    plt.grid(linestyle='--', which='both')

    ax.plot(value1, label=label1, linewidth=2, color='r', alpha=0.7)
    ax.plot(value2, label=label2, linewidth=2, color='b', linestyle='--',
            alpha=0.7)
    '''
    ax.legend(loc='upper right', frameon=True, ncol=1,
              handlelength=5, borderpad=1.3,
              labelspacing=1.3, shadow=False, fontsize='x-large')
    '''
    plt.legend(loc=legend_pos, prop=font_legend)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Time (h)", font_label)
    ax.set_ylabel(ylabel, font_label)
    ax.set_ylim(ymax=max(max(value1), max(value2)) * n)
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def plot_three_lines(csv_file, comp1, comp2, comp3, label1, label2, label3,
                     titel, ylabel, c1='r', c2='b', c3='g', l1='-', l2='-',
                     l3='-', n=1.1, legend_pos='best'):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', titel)
    df = pd.read_csv(csv_file)

    data1 = df[(df['var'].str.contains(comp1))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains(comp2))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[(df['var'].str.contains(comp3))]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    plt.grid(linestyle='--', which='both')

    ax.plot(value1, label=label1, linewidth=2, alpha=0.7,
            color=c1, linestyle=l1)
    ax.plot(value2, label=label2, linewidth=2, alpha=0.7,
            color=c2, linestyle=l2)
    ax.plot(value3, label=label3, linewidth=2, alpha=0.7,
            color=c3, linestyle=l3)

    plt.legend(loc=legend_pos, prop=font_legend)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Time (h)", font_label)
    ax.set_ylabel(ylabel, font_label)
    ax.set_ylim(ymax=max(max(value1), max(value2), max(value3)) * n)
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def plot_four_lines(csv_file, comp1, comp2, comp3, comp4, label1, label2,
                    label3, label4, titel, ylabel, c1='r', c2='b', c3='g',
                    c4='k', l1='-', l2='-', l3='--', l4='--', n=1.1,
                    legend_pos='best'):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', titel)
    df = pd.read_csv(csv_file)

    data1 = df[(df['var'].str.contains(comp1))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains(comp2))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[(df['var'].str.contains(comp3))]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data4 = df[(df['var'].str.contains(comp4))]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    ax.plot(value1, label=label1, linewidth=2, alpha=0.7,
            color=c1, linestyle=l1)
    ax.plot(value2, label=label2, linewidth=2, alpha=0.7,
            color=c2, linestyle=l2)
    ax.plot(value3, label=label3, linewidth=2, alpha=0.7,
            color=c3, linestyle=l3)
    ax.plot(value4, label=label4, linewidth=2, alpha=0.7,
            color=c4, linestyle=l4)

    plt.legend(loc=legend_pos, prop=font_legend)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Time (h)", font_label)
    ax.set_ylabel(ylabel, font_label)
    ax.set_ylim(ymax=max(max(value1), max(value2), max(value3)) * n)
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_one_line(csv_file, time_step, comp, titel, ylabel, bld, n=1.1):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, titel)
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data = df[(df['var'].str.contains(comp))]
    data = data.reset_index(drop=True)
    value = data['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    ax.step(time_steps, value, where="post", linestyle='-', color='r',
            linewidth=2, zorder=1.5)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(ylabel, font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(value) * n)
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()
    plt.savefig(plot_output)


def step_plot_two_lines(csv_file, time_step, comp1, comp2, label1, label2,
                        titel, ylabel, bld, n=1.1, legend_pos='best'):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, titel)
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains(comp1))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains(comp2))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    ax.step(time_steps, value1, label=label1, where="post", linestyle='-',
            color='r', linewidth=2)
    ax.step(time_steps, value2, label=label2, where="post", linestyle='--',
            color='b', linewidth=2)

    plt.legend(loc=legend_pos, prop=font_legend)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(ylabel, font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(value1), max(value2)) * n)
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_three_lines(csv_file, time_step, comp1, comp2, comp3, label1,
                          label2, label3, titel, ylabel, bld, c1='r', c2='b',
                          c3='g', l1='-', l2='-', l3='-', n=1.1,
                          legend_pos='best'):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, '1')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains(comp1))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains(comp2))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[(df['var'].str.contains(comp3))]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.grid(linestyle='--', which='both', alpha=0.6)

    ax.step(time_steps, value1, where="post", label=label1,
            linestyle=l1, color=c1, linewidth=2, alpha=0.7)
    ax.step(time_steps, value2, where="post", label=label2,
            linestyle=l2, color=c2, linewidth=2, alpha=0.7)
    ax.step(time_steps, value3, where="post", label=label3,
            linestyle=l3, color=c3, linewidth=2, alpha=0.7)

    plt.legend(loc=legend_pos, prop=font_legend)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(ylabel, font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(value1), max(value2), max(value3)) * n)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_four_lines(csv_file, time_step, comp1, comp2, comp3, comp4,
                         label1, label2, label3, label4, titel, ylabel, bld, c1='r',
                         c2='b', c3='g', c4='k', l1='-', l2='-', l3='--',
                         l4='--', n=1.1, legend_pos='best'):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, titel)
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains(comp1))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains(comp2))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[(df['var'].str.contains(comp3))]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data4 = df[(df['var'].str.contains(comp4))]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    ax.step(time_steps, value1, label=label1, where="post", linestyle=l1,
            color=c1, linewidth=2, alpha=0.7)
    ax.step(time_steps, value2, label=label2, where="post", linestyle=l2,
            color=c2, linewidth=2, alpha=0.7)
    ax.step(time_steps, value3, label=label3, where="post", linestyle=l3,
            color=c3, linewidth=2, alpha=0.7)
    ax.step(time_steps, value4, label=label4, where="post", linestyle=l4,
            color=c4, linewidth=2, alpha=0.7)

    plt.legend(loc=legend_pos, prop=font_legend)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(ylabel, font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(value1), max(value2), max(value3)) * n)
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def print_size(csv_file):
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    size_dict = {}
    for element in elements_dict:
        if len(elements_dict[element]) == 1:
            if 'size' in element and not np.isnan(elements_dict[element][0]):
                size_dict[element] = elements_dict[element][0]
                print(element, ' = ', size_dict[element])
    for element in elements_dict:
        if len(elements_dict[element]) == 1:
            if 'annual_cost_bld' in element and not \
                    np.isnan(elements_dict[element][0]):
                size_dict[element] = elements_dict[element][0]
                print('annual_cost = ', size_dict[element])
            if 'operation_cost_bld' in element and not \
                    np.isnan(elements_dict[element][0]):
                size_dict[element] = elements_dict[element][0]
                print('operation_cost = ', size_dict[element])


def step_plot_water_tes(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'Diagramm des Speichers')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('temp_water_tes')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('input_heat_water_tes')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('output_heat_water_tes')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.set_ylim(ymax=105)
    ax.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Diagramm des Solarspeichers', font_titel, y=1.02)
    ax.step(time_steps, value1, where="post", label='Temperatur',
                   linestyle='-', color='k', linewidth=1)
    ax2 = ax.twinx()
    ax2.step([], [], where="post", label='Temperatur',
             color='k', linewidth=1, alpha=0.5)
    ax2.step(time_steps, value2, where="post",
                    color='r', linewidth=0.1, alpha=0.5)
    ax2.fill_between(time_steps, value2, 0, facecolor='r', label='Input',
                    zorder=10, step="post", alpha=0.5)
    ax2.step(time_steps, value3, where="post",
                    color='b', linewidth=0.1, alpha=0.5)
    ax2.fill_between(time_steps, value3, 0, facecolor='b', label='Output',
                    zorder=10, step="post", alpha=0.5)
    ax2.set_ylim(ymin=0, ymax=250)

    plt.legend(loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    ax2.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_water_tes_demand(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'water_tes-cns')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('temp_water_tes')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('input_heat_therm_cns')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('input_heat_hw_cns')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data5 = df[df['var'].str.contains('input_elec_e_boi')]
    data5 = data5.reset_index(drop=True)
    value5 = data5['value']
    value6 = value2 + value3 - value5
    value4 = value2 + value3

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.yaxis.set_minor_locator(MultipleLocator(5))
    ax.set_ylim(ymin=0,  ymax=110)
    ax.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Diagramm des Solarspeichers', font_titel, y=1.02)
    ax.step(time_steps, value1, where="post", label='Temperatur',
                   linestyle='-', color='k', linewidth=1)
    ax2 = ax.twinx()
    ax2.step([], [], where="post", label='Temperatur',
             color='k', linewidth=1, alpha=0.5)
    ax2.step(time_steps, value2, where="post",
                    color='r', linewidth=0.1, alpha=0.5)
    ax2.fill_between(time_steps, value2, 0, facecolor='r', label='Wärmebedarf',
                    zorder=10, step="post", alpha=0.5)
    ax2.step(time_steps, value4, where="post",
                    color='b', linewidth=0.1, alpha=0.5)
    ax2.fill_between(time_steps, value4, value2, facecolor='b', label='Warmwasserbedarf',
                    zorder=10, step="post", alpha=0.5)
    ax2.step(time_steps, value6, where="post",
                    color='b', linewidth=0.1, alpha=0.5)
    ax2.fill_between(time_steps, value4, value6, facecolor='g', hatch='///', label='EHK',
                    zorder=10, step="post", alpha=0.5)
    ax2.set_ylim(ymin=0, ymax=300)

    plt.legend(loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    ax2.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_demand_e_boi(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'cns-e_boi')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('tp_val_hw_e_boi_temp')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('input_heat_hw_cns')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('input_elec_e_boi')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.set_ylim(ymin=0,  ymax=120)
    ax.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Diagramm des Solarspeichers', font_titel, y=1.02)
    ax.step(time_steps, value1, where="post", label='tp_val_hw_e_boi_temp',
                   linestyle='-', color='k', linewidth=1)

    ax2 = ax.twinx()
    ax2.step([], [], where="post", label='tp_val_hw_e_boi_temp',
             color='k', linewidth=1, alpha=0.5)
    ax2.step(time_steps, value2, where="post",
                    color='r', linewidth=0.5, alpha=0.5)
    ax2.fill_between(time_steps, value2, 0, facecolor='r', label='input_heat_hw_cns',
                    zorder=10, step="post", alpha=0.5)
    ax2.step(time_steps, value3, where="post",
                    color='b', linewidth=0.5, alpha=0.5)
    ax2.fill_between(time_steps, value3, 0, facecolor='b', label='input_elec_e_boi',
                    zorder=10, step="post", alpha=0.5)
    ax2.set_ylim(ymin=0, ymax=300)

    plt.legend(loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    ax2.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_chp(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Energieversorgung')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains('output_heat_water_tes'))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains('output_heat_boi'))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[(df['var'].str.contains('input_heat_hw_cns'))]['value']
    data3 = data3.reset_index(drop=True)
    data4 = df[(df['var'].str.contains('input_heat_therm_cns'))]['value']
    data4 = data4.reset_index(drop=True)
    data5 = data3 + data4

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    ax.step(time_steps, value1, where="post", label='Wärme aus Speicher',
            linewidth=2, alpha=0.7, color='r', linestyle='-')
    ax.step(time_steps, value2, where="post", label='Wärme aus Kessel',
            linewidth=2, alpha=0.7, color='b', linestyle='-')
    ax.step(time_steps, data5, where="post", label='Gesamter Wärmebedarf',
            linewidth=2, alpha=0.7, color='k', linestyle='--')

    plt.legend(loc='best', prop=font_legend)
    #ax.set_title('Energieversorgung', font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r'Leistung (kW)', font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(value1), max(value2), max(data5)) * 1.5)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_chp_small_eff(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'Thermischer Wirkungsgrad des BHKW')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('inlet_temp_chp')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('therm_eff_chp')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Thermischer Wirkungsgrad des BHKW', font_titel, y=1.02)
    lns1 = ax.step(time_steps, value1, where="post",
                   label='Eintrittstemperatur',
                   linestyle='--', color='k', linewidth=2)
    ax2 = ax.twinx()
    lns2 = ax2.step(time_steps, value2, where="post",
                    label='Thermischer Wirkungsgrad',
                    color='r', linewidth=2, alpha=0.7)
    ax.set_ylim(ymax=max(value1) * 1.3)
    lns = lns1 + lns2
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    ax2.set_ylabel(r"Wirkungsgrad", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_chp_big_eff(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'Thermischer Wirkungsgrad des BHKW')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('inlet_temp_chp')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('outlet_temp_chp')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('therm_eff_chp')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Thermischer Wirkungsgrad des BHKW', font_titel, y=1.02)
    lns1 = ax.step(time_steps, value1, where="post",
                   label='Thermischer Wirkungsgrad',
                   linestyle='--', color='k', linewidth=2)
    ax2 = ax.twinx()
    lns2 = ax2.step(time_steps, value2, where="post",
                    label='Eintrittstemperatur',
                    color='r', linewidth=2, alpha=0.7)
    lns3 = ax2.step(time_steps, value3, where="post",
                    label='Austrittstemperatur',
                    color='b', linewidth=2, alpha=0.7)
    ax.set_ylim(ymax=max(max(value2), max(value3)) * 1.3)
    lns = lns1 + lns2 + lns3
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Wirkungsgrad", font_label)
    ax2.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_solar_eff(csv_file, time_step, temp_profile, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'Wirkungsgrad des Kollektors')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('eff_solar_coll')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('inlet_temp_solar_coll')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('outlet_temp_solar_coll')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data4 = pd.DataFrame(temp_profile)
    data4 = data4.reset_index(drop=True)
    value4 = data4[0]

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.yaxis.set_minor_locator(MultipleLocator(5))
    ax.set_ylim(ymin=0)
    ax.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Wirkungsgrad des Kollektors', font_titel, y=1.02)
    lns1 = ax.step(time_steps, value1, where="post",
                   label='Wirkungsgrad',
                   linestyle='-', color='k', linewidth=2)
    ax2 = ax.twinx()
    lns2 = ax2.step(time_steps, value2, where="post",
                    label='Eintrittstemperatur',
                    color='r', linewidth=2, alpha=0.7)
    lns3 = ax2.step(time_steps, value3, where="post",
                    label='Austrittstemperatur', linestyle='--',
                    color='b', linewidth=2, alpha=0.7)
    lns4 = ax2.step(time_steps, value4, where="post",
                    label='Umgebungstemperatur', linestyle='-',
                    color='g', linewidth=2, alpha=0.7)
    ax2.yaxis.set_minor_locator(MultipleLocator(10))
    ax2.set_ylim(ymin=-10, ymax=max(max(value2), max(value3)) * 2)
    lns = lns1 + lns2 + lns3 + lns4
    labs = [l.get_label() for l in lns]

    plt.legend(lns, labs, prop=font_legend, loc='best')

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Wirkungsgrad", font_label)
    ax2.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_solar_irr(csv_file, time_step, irr_profile, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'Wirkungsgrad ')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = pd.DataFrame(irr_profile)
    data1 = data1.reset_index(drop=True)
    value1 = data1[0]
    data2 = df[df['var'].str.contains('inlet_temp_solar_coll')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('outlet_temp_solar_coll')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.set_ylim(ymax=1000)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Wirkungsgrad des Kollektors', font_titel, y=1.02)
    lns1 = ax.step(time_steps, value1, where="post",
                   label='Strahlung',
                   linestyle='-', color='k', linewidth=2)
    ax2 = ax.twinx()
    lns2 = ax2.step(time_steps, value2, where="post",
                    label='Eintrittstemperatur',
                    color='r', linewidth=2, alpha=0.7)
    lns3 = ax2.step(time_steps, value3, where="post",
                    label='Austrittstemperatur', linestyle='--',
                    color='b', linewidth=2, alpha=0.7)

    lns = lns1 + lns2 + lns3
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    ax2.set_ylim(ymin=0, ymax=max(max(value2), max(value3)) * 1.1)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Strahlung (W/h)", font_label)
    ax2.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_two_lines_color(csv_file, time_step, comp1, comp2, label1, label2,
                              titel, ylabel, bld, n=1.1, legend_pos='best'):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, titel)
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains(comp1))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains(comp2))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both', zorder=0)

    ax.step(time_steps, value1, where="post", color='b', linewidth=0.2)
    ax.fill_between(time_steps, value1, 0, facecolor='b', label=label1,
                    zorder=10, step="post")
    ax.step(time_steps, value2, where="post", color='r', linewidth=0.2)
    ax.fill_between(time_steps, value2, value1, facecolor='r', label=label2,
                    zorder=10, step="post")

    plt.legend(loc=legend_pos, prop=font_legend)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(ylabel, font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(value1), max(value2)) * n)
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_solar_water_tes_color(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'Diagramm vom Solarspeicher')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('water_tes_tp_val_temp')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('input_heat_water_tes')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('output_heat_water_tes')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.set_ylim(ymin=10, ymax=75)
    ax.grid(linestyle='--', which='both', zorder=0)

    plt.xticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    #ax.set_title('Diagramm des Solarspeichers', font_titel, y=1.02)
    lns1 = ax.step(time_steps, value1, where="post", label='Temperatur',
                   linestyle='-', color='k', linewidth=1, zorder=10)
    ax2 = ax.twinx()
    ax2.step(time_steps, value2, where="post", linewidth=1,
             label='Input', alpha=0)
    ax2.step(time_steps, value3, where="post", linewidth=1,
             label='Output', alpha=0)
    lns2 = ax2.plot([], [], linewidth=1, label='Input', color='r', alpha=0.5)
    lns3 = ax2.plot([], [], linewidth=1, label='Output', color='b', alpha=0.5)
    ax2.fill_between(time_steps, value2, 0, facecolor='r', step="post",
                     zorder=10, alpha=0.5)
    ax2.fill_between(time_steps, value3, 0, facecolor='b', step="post",
                     zorder=10, alpha=0.5)
    ax2.set_ylim(ymax=max(max(value2), max(value3)) * 1.5)

    lns = lns1 + lns2 + lns3
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    ax2.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_heat_demand_color(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Wärme- und Warmwasserbedarf')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data3 = df[(df['var'].str.contains('input_heat_hw_cns'))]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data4 = df[(df['var'].str.contains('input_heat_therm_cns'))]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']
    data5 = value3 + value4

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(1, 1, 1)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.grid(linestyle='--', which='both', alpha=0.6)

    ax.step(time_steps, value3, where="post", color='b', linewidth=0.2)
    ax.fill_between(time_steps, value3, 0, facecolor='b',
                    label='Warmwasserbedarf', zorder=10, step="post")
    ax.step(time_steps, data5, where="post", color='r', linewidth=0.2)
    ax.fill_between(time_steps, data5, value3, facecolor='r',
                    label='Heizungsbedarf', zorder=10, step="post")

    plt.legend(loc='best', prop=font_legend)
    #ax.set_title('Wärme- und Warmwasserbedarf', font_titel, y=1.02)
    ax.set_xlabel('Stunde (h)', font_label)
    ax.set_ylabel('Leistung (kW)', font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(value3), max(value4), max(data5)) * 1.3)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    ax.set_axisbelow(True)
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_chp_color(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Energieversorgung')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains('output_heat_water_tes'))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    # data2 = df[(df['var'].str.contains('output_heat_boi'))]
    # data2 = data2.reset_index(drop=True)
    # value2 = data2['value']
    data3 = df[(df['var'].str.contains('input_heat_hw_cns'))]['value']
    data3 = data3.reset_index(drop=True)
    data4 = df[(df['var'].str.contains('input_heat_therm_cns'))]['value']
    data4 = data4.reset_index(drop=True)
    data5 = data3 + data4

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    ax.step(time_steps, value1, where="post", color='r', linewidth=0.1)
    ax.fill_between(time_steps, value1, 0, facecolor='r',
                    label='Wärme aus BHKW', zorder=10, step="post")
    ax.step(time_steps, data5, where="post", color='b', linewidth=0.1)
    ax.fill_between(time_steps, data5, value1, facecolor='b',
                    label='Wärme aus Kessel', zorder=10, step="post")

    plt.legend(loc='best', prop=font_legend)
    #ax.set_title('Energieversorgung', font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r'Leistung (kW)', font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(value1), max(data5)) * 1.5)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_chp_diagram_color(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'demand')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains('output_heat_chp'))]['value']
    data1 = data1.reset_index(drop=True)
    df1 = pd.DataFrame(data1)
    df1.sort_values(by=df1.columns[0], axis=0, ascending=False, inplace=True)
    ts1 = pd.Series(df1['value'].values, index=time_steps)
    data3 = df[(df['var'].str.contains('input_heat_hw_cns'))]['value']
    data3 = data3.reset_index(drop=True)
    data4 = df[(df['var'].str.contains('input_heat_therm_cns'))]['value']
    data4 = data4.reset_index(drop=True)
    data5 = data3 + data4
    df2 = pd.DataFrame(data5)
    df2.sort_values(by=df2.columns[0], axis=0, ascending=False, inplace=True)
    ts2 = pd.Series(df2['value'].values, index=time_steps)

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    ax.step(time_steps, ts1, where="post", color='r', linewidth=0.2)
    ax.fill_between(time_steps, ts1, 0, facecolor='r',
                    zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, ts2, where="post", color='b', linewidth=0.2)
    ax.fill_between(time_steps, ts2, 0, facecolor='b',
                    zorder=10, step="post", alpha=0.5)
    ax.plot([], [], linewidth=8, label='Wärme aus BHKW', color='r',
            alpha=0.5)
    ax.plot([], [], linewidth=8, label='Gesamter Wärmebedarf', color='b',
            alpha=0.5)

    plt.legend(loc='best', prop=font_legend)

    #ax.set_title('Test', font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel('demand', font_label)
    ax.set_xlim(xmin=0)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()
    plt.savefig(plot_output)


def step_plot_chp_energy_color(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'Energieerzeugung mit BHKW')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('temp_water_tes')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('input_heat_water_tes')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('output_heat_water_tes')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data4 = df[df['var'].str.contains('output_heat_boi_s')]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']
    value5 = value4 + value3

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.set_ylim(ymin=0, ymax=120)
    ax.grid(linestyle='--', which='both', zorder=0)

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Energieerzeugung', font_titel, y=1.02)
    lns1 = ax.step(time_steps, value1, where="post",
                   label='Temperatur des Speichers',
                   linestyle='-', color='k', linewidth=1, zorder=10)
    ax2 = ax.twinx()
    ax2.step(time_steps, value2, where="post", linewidth=0.1,
             label='Input', alpha=0)
    ax2.fill_between(time_steps, value2, 0, facecolor='r', step="post",
                     zorder=10, alpha=0.5)
    ax2.step(time_steps, value3, where="post", linewidth=0.1,
             label='Output', alpha=0)
    ax2.fill_between(time_steps, value3, 0, facecolor='b', step="post",
                     zorder=10, alpha=0.5)
    ax2.step(time_steps, value4, where="post", linewidth=0.1,
             label='Wärme aus Kessel', alpha=0)
    ax2.fill_between(time_steps, value5, value3, facecolor='g', step="post",
                     zorder=10, alpha=0.5)
    lns2 = ax2.plot([], [], linewidth=8, label='Input', color='r', alpha=0.5)
    lns3 = ax2.plot([], [], linewidth=8, label='Output', color='b', alpha=0.5)
    lns4 = ax2.plot([], [], linewidth=8, label='Wärme aus Kessel', color='g',
                    alpha=0.5)

    ax2.set_ylim(ymax=max(max(value2), max(value3)) * 1.5)

    lns = lns1 + lns2 + lns3 + lns4
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    ax2.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_chp_water_tes_color(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'BHKW')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('temp_water_tes')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('input_heat_water_tes')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('output_heat_water_tes')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.set_ylim(ymin=0, ymax=120)
    ax.grid(linestyle='--', which='both', zorder=0)

    plt.xticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    #ax.set_title('Diagramm des Speicher', font_titel, y=1.02)
    lns1 = ax.step(time_steps, value1, where="post",
                   label='Temperatur',
                   linestyle='-', color='k', linewidth=1, zorder=10)
    ax2 = ax.twinx()
    ax2.step(time_steps, value2, where="post", linewidth=0.1,
             label='Input', alpha=0)
    ax2.fill_between(time_steps, value2, 0, facecolor='r', step="post",
                     zorder=10, alpha=0.5)
    ax2.step(time_steps, value3, where="post", linewidth=0.1,
             label='Output', alpha=0)
    ax2.fill_between(time_steps, value3, 0, facecolor='b', step="post",
                     zorder=10, alpha=0.5)
    lns2 = ax2.plot([], [], linewidth=1, label='Input', color='r', alpha=0.5)
    lns3 = ax2.plot([], [], linewidth=1, label='Output', color='b', alpha=0.5)

    ax2.set_ylim(ymax=max(max(value2), max(value3)) * 1.5)

    lns = lns1 + lns2 + lns3
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    ax2.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_heat_demand_color(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Energieerzeugung')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('output_heat_chp')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('output_heat_boi_s')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data4 = df[df['var'].str.contains('input_elec_e_boi')]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']
    data5 = df[df['var'].str.contains('input_heat_therm_cns')]
    data5 = data5.reset_index(drop=True)
    value5 = data5['value']
    data6 = df[df['var'].str.contains('input_heat_hw_cns')]
    data6 = data6.reset_index(drop=True)
    value6 = data6['value']
    value7 = value5 + value6
    value8 = value1 + value2
    value9 = value8 + value4



    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Energieerzeugung', font_titel, y=1.02)


    lns1 = ax.step(time_steps, value7, where="post", label='gesamter Wärmebedarf',
                   linestyle='-', color='k', linewidth=1, zorder=10)
    ax.step(time_steps, value1, where="post", color='r', linestyle='-', linewidth=0.1)
    ax.fill_between(time_steps, value1, 0, facecolor='r',
                     zorder=10, step="post", alpha=1)
    ax.step(time_steps, value8, where="post", color='b', linewidth=0.1)
    ax.fill_between(time_steps, value8, value1, facecolor='b',
                     zorder=10, step="post", alpha=1)
    ax.step(time_steps, value9, where="post", color='xkcd:green', linewidth=0.1)
    ax.fill_between(time_steps, value9, value8, facecolor='xkcd:green',
                    zorder=10, step="post", alpha=1)
    lns2 = ax.plot([], [], linewidth=1, label='Wärme aus BHKW',
                    color='r', alpha=1)
    lns3 = ax.plot([], [], linewidth=1, label='Wärme aus HK',
                    color='b', alpha=1)
    lns5 = ax.plot([], [], linewidth=1, label='Wärme aus EHK',
                   color='xkcd:orange', alpha=1)

    lns = lns3 + lns5
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=270)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_chp_diagram_color1(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'demand')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains('output_heat_chp'))]['value']
    df1 = pd.DataFrame(data1)
    s = df1['value'].sum() / len(time_steps)
    df1.sort_values(by=df1.columns[0], axis=0, ascending=False, inplace=True)
    ts1 = pd.Series(df1['value'].values, index=time_steps)
    data3 = df[(df['var'].str.contains('input_heat_hw_cns'))]['value']
    data3 = data3.reset_index(drop=True)
    data4 = df[(df['var'].str.contains('input_heat_therm_cns'))]['value']
    data4 = data4.reset_index(drop=True)
    data5 = data3 + data4
    df2 = pd.DataFrame(data5)
    df2.sort_values(by=df2.columns[0], axis=0, ascending=False, inplace=True)
    ts2 = pd.Series(df2['value'].values, index=time_steps)

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    if name=='b':
        ax.xaxis.set_major_locator(MultipleLocator(24))
    else:
        ax.xaxis.set_major_locator(MultipleLocator(12))
    plt.grid(linestyle='--', which='both')

    ax.hlines(s, 0, len(time_steps), color='g', linewidth=0.2, alpha=0)
    ax.fill_between(time_steps, s, 0, facecolor='g', hatch='///',
                    label='Durchschnittswärme aus BHKW',
                    zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, ts1, where="post", color='r', linewidth=0.2)
    ax.fill_between(time_steps, ts1, 0, facecolor='r', label='Wärme aus BHKW',
                    zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, ts2, where="post", color='b', linewidth=0.2)
    ax.fill_between(time_steps, ts2, 0, facecolor='b',
                    label='Gesamter Wärmebedarf',
                    zorder=10, step="post", alpha=0.5)

    plt.legend(loc='best', prop=font_legend)

    #ax.set_title('Test', font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel('demand', font_label)
    ax.set_xlim(xmin=0)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()
    plt.savefig(plot_output)


def step_plot_status(csv_file, start_time, time_step, bld, name,
                     n=1.1):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Status des BHKW')
    df = pd.read_csv(csv_file)

    data = df[(df['var'].str.contains('status_chp'))]
    data = data.reset_index(drop=True)
    value = data['value'][start_time:start_time + time_step]
    value = value.reset_index(drop=True)

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    plt.grid(linestyle='--', which='both')

    ax.step(range(start_time - 1, start_time + time_step - 1), value,
            where="post",
            linestyle='-', color='r', linewidth=0.1, zorder=1.5)
    ax.fill_between(range(start_time - 1, start_time + time_step - 1), value, 0,
                    facecolor='r', label='Wärme aus BHKW',
                    zorder=10, step="post", alpha=0.5)
    # todo(qli): noch vertikale Linien hinzufügen
    # Der erste Parameter ist die Y-Koordinate.
    #ax.vlines(0, 0, 1, linestyle='-', color='r', linewidth=2, zorder=1.5)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel('Status', font_label)
    ax.set_xlim(xmin=0, xmax=196)
    ax.set_ylim(ymax=max(value) * n)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()
    plt.savefig(plot_output)


def step_plot_heat_water_tes(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Wärmeerzeugung')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('output_heat_chp')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('output_heat_boi_s')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('output_heat_boi_c')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data4 = df[df['var'].str.contains('output_heat_heat_pump')]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']
    data5 = df[df['var'].str.contains('output_heat_heat_ex')]
    data5 = data5.reset_index(drop=True)
    value5 = data5['value']
    data6 = df[df['var'].str.contains('output_heat_water_tes')]
    data6 = data6.reset_index(drop=True)
    value6 = data6['value']
    value7 = value1 + value2
    value8 = value7 + value3
    value9 = value8 + value4
    value10 = value9 + value5

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Energieerzeugung', font_titel, y=1.02)
    ax.step(time_steps, value1, where="post",
            linestyle='-.', color='r', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value1, 0, facecolor='r',
                    zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, value7, where="post",
            linestyle='-.', color='r', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value7, value1, facecolor='g',
                    zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, value8, where="post",
            linestyle='-', color='y', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value8, value7, facecolor='y',
                    zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, value9, where="post",
            linestyle='-', color='b', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value9, value8, facecolor='b',
                    zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, value10, where="post",
            linestyle='-', color='m', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value10, value9, facecolor='m',
                    zorder=10, step="post", alpha=0.5)
    lns6 = ax.step(time_steps, value6, where="post", label='Direkt genutzte '
                                                           'Wärme',
                   linestyle='-', color='k', linewidth=1, zorder=10)

    lns1 = ax.plot([], [], linewidth=1, label='Wärme aus BHKW',
                   color='r', alpha=0.5)
    lns2 = ax.plot([], [], linewidth=1, label='Wärme aus Heizkessel',
                   color='g', alpha=0.5)
    lns3 = ax.plot([], [], linewidth=1, label='Wärme aus Brennwertkessel',
                   color='y', alpha=0.5)
    lns4 = ax.plot([], [], linewidth=1, label='Wärme aus Wärmepumpe',
                   color='b', alpha=0.5)
    lns5 = ax.plot([], [], linewidth=1, label='Wärme aus Solarthermie',
                   color='m', alpha=0.5)

    lns = lns1 + lns2 + lns3 + lns4 + lns5 + lns6
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_heat_speicher(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Wärmedirektnutzung und -speicher')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('output_heat_chp')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('output_heat_boi_s')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data4 = df[df['var'].str.contains('output_heat_heat_pump')]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']
    data5 = df[df['var'].str.contains('output_heat_heat_ex')]
    data5 = data5.reset_index(drop=True)
    value5 = data5['value']
    data6 = df[df['var'].str.contains('output_heat_water_tes')]
    data6 = data6.reset_index(drop=True)
    value6 = data6['value']
    value7 = value1 + value2 + value4 + value5 - value6

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')
    ax.fill_between(time_steps, value7, 0, facecolor='r',
                    zorder=10, step="post", alpha=0.5)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Energiespeicher', font_titel, y=1.02)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_elec(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Stromerzeugung')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('output_elec_e_meter')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('input_elec_e_boi')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('input_elec_heat_pump')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data4 = df[df['var'].str.contains('input_elec_e_cns')]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']
    value6 = value1 - value2 - value3 - value4

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Stromerzeugung', font_titel, y=1.02)
    ax.step(time_steps, value6, where="post", label='Strom Eigenerzeugung',
            linestyle='-.', color='k', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value6, 0, facecolor='r',
                    zorder=10, step="post", alpha=0.5)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    lns = ax.plot([], [], linewidth=8, label='Strom aus Stromnetz',
                   color='r', alpha=0.5)
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_elec_bilanz(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Strombilanz')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('output_elec_chp')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('output_elec_pv')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('input_elec_e_boi')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data4 = df[df['var'].str.contains('input_elec_heat_pump')]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']
    data5 = df[df['var'].str.contains('input_elec_e_cns')]
    data5 = data5.reset_index(drop=True)
    value5 = data5['value']

    value7 = value1 + value2
    value8 = value4 + value3
    value9 = value8 + value5

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Energieerzeugung', font_titel, y=1.02)
    #ax.hlines(value1, 0, len(time_steps), linewidth=0.2, alpha=0)
    ax.fill_between(time_steps, value1, 0, hatch='//', linestyle='-', color='k',
                    label='Strom aus BHKW',
                    zorder=20, step="post", alpha=0)
    ax.step(time_steps, value1, where="post",
            linestyle='-', color='k', linewidth=0.1, zorder=20)
    #ax.hlines(value7, value1, len(time_steps), linewidth=0.2, alpha=0)
    ax.step(time_steps, value7, where="post",
            linestyle='-', color='k', linewidth=0.1, zorder=20)
    ax.fill_between(time_steps, value7, value1, hatch='///', linestyle='-', color='k',
                           label='Strom aus PV',
                           zorder=20, step="post", alpha=0)
    ax.fill_between(time_steps, value3, 0, facecolor='r', label='Strombedarf von EHK',
                    zorder=10, step="post", alpha=1)
    ax.fill_between(time_steps, value8, value3, facecolor='g',label='Strombedarf von WP',
                    zorder=10, step="post", alpha=1)
    ax.fill_between(time_steps, value9, value8, facecolor='b', label='Sonstiger Strombedarf',
                    zorder=10, step="post", alpha=1)

    plt.legend(loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_chp_last(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'last')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data3 = df[(df['var'].str.contains('input_heat_hw_cns'))]['value']
    data3 = data3.reset_index(drop=True)
    data4 = df[(df['var'].str.contains('input_heat_therm_cns'))]['value']
    data4 = data4.reset_index(drop=True)
    data5 = data3 + data4
    df2 = pd.DataFrame(data5)
    df2.sort_values(by=df2.columns[0], axis=0, ascending=False, inplace=True)
    ts2 = pd.Series(df2['value'].values, index=time_steps)

    data1 = df[(df['var'].str.contains('output_heat_chp'))]['value']
    data1 = data1.reset_index(drop=True)
    df1 = pd.DataFrame(data1)
    df1.sort_values(by=df1.columns[0], axis=0, ascending=False, inplace=True)
    ts1 = pd.Series(df1['value'].values, index=time_steps)


    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    ax.step(time_steps, ts1, where="post", color='r', linewidth=0.2)
    ax.fill_between(time_steps, ts1, 0, facecolor='r',
                    zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, ts2, where="post", color='b', linewidth=0.2)
    ax.fill_between(time_steps, ts2, 0, facecolor='b',
                    zorder=10, step="post", alpha=0.5)
    ax.plot([], [], linewidth=8, label='Wärme aus BHKW', color='r',
            alpha=0.5)
    ax.plot([], [], linewidth=8, label='Gesamter Wärmebedarf', color='b',
            alpha=0.5)

    plt.legend(loc='best', prop=font_legend)

    #ax.set_title('1', font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel('demand', font_label)
    ax.set_xlim(xmin=0)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()
    plt.savefig(plot_output)

def step_plot_test_qli(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Test')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('temp_water_tes')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('heat_tp_val_therm_cns')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Test', font_titel, y=1.02)
    lns1 = ax.step(time_steps, value1, where="post",
                   label='temp_water_tes',
                   linestyle='--', color='k', linewidth=2)
    ax2 = ax.twinx()
    lns2 = ax2.step(time_steps, value2, where="post",
                    label='heat_tp_val_therm_cns',
                    color='r', linewidth=2, alpha=0.7)
    ax.set_ylim(ymax=max(value1) * 1.3)
    lns = lns1 + lns2
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Temperatur ($^\circ$C)", font_label)
    ax2.set_ylabel(r'Leistung (kW)', font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_heat_1(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Energieerzeugung')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data2 = df[df['var'].str.contains('output_heat_boi_s')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data4 = df[df['var'].str.contains('input_elec_e_boi')]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']
    data5 = df[df['var'].str.contains('input_heat_therm_cns')]
    data5 = data5.reset_index(drop=True)
    value5 = data5['value']
    data6 = df[df['var'].str.contains('input_heat_hw_cns')]
    data6 = data6.reset_index(drop=True)
    value6 = data6['value']
    data9 = df[df['var'].str.contains('loss_water_tes')]
    data9 = data9.reset_index(drop=True)
    value9 = data9['value']
    value7 = value2 + value4
    value8 = value5 + value6
    value10 = value7 - value9


    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Energieerzeugung', font_titel, y=1.02)

    ax.step(time_steps, value5, where="post", label='Wärmebedarf',
                   linestyle='-', color='k', linewidth=1, zorder=10)
    ax.step(time_steps, value8, where="post", label='gesamter Wärmebedarf',
                   linestyle='-', color='k', linewidth=1, zorder=10)
    ax.step(time_steps, value2, where="post", color='r', linestyle='-', linewidth=0.1)
    ax.fill_between(time_steps, value2, 0, facecolor='r', label='Wärme aus HK',
                     zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, value7, where="post", color='b', linewidth=0.1)
    ax.fill_between(time_steps, value7, value2, facecolor='b', label='Wärme aus EHK',
                     zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, value10, where="post", color='k', linewidth=0.1)
    ax.fill_between(time_steps, value7, value10, where=value7>= value10, facecolor='w', hatch='/// ',
                    label='Verlust', zorder=10, step="post", alpha=0.5)


    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=210)
    plt.xticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    plt.legend(loc='best', prop=font_legend)
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_elec_1(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Stromerzeugung')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('output_elec_pv')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('input_elec_e_boi')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('input_elec_bat')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data4 = df[df['var'].str.contains('input_elec_e_cns')]
    data4 = data4.reset_index(drop=True)
    value4 = data4['value']
    value5 = value2 + value4
    value6 = value5 + value3

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Stromerzeugung', font_titel, y=1.02)
    ax.step(time_steps, value1, where="post", label='Strom Eigenerzeugung',
            linestyle='-', color='k', linewidth=1, zorder=20)

    ax.step(time_steps, value2, where="post",
            linestyle='-', color='r', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value2, 0, facecolor='r', label='EHK Strombedarf',
                    zorder=10, step="post", alpha=0.5)

    ax.step(time_steps, value5, where="post",
            linestyle='-', color='b', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value5, value2, facecolor='b', label='sonstiger Strombedarf',
                    zorder=10, step="post", alpha=0.5)

    ax.step(time_steps, value6, where="post",
            linestyle='-', color='g', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value6, value5, facecolor='g', label='Stromspeicher',
                    zorder=10, step="post", alpha=0.5)



    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.legend(loc='best', prop=font_legend)
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_tp_val(csv_file, time_step, bld, name):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, name)
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains('heat_water_tes_tp_val_hw'))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains('heat_tp_val_hw_e_boi'))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[(df['var'].str.contains('input_elec_e_boi'))]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']
    data3 = df[(df['var'].str.contains('input_heat_hw_cns'))]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.grid(linestyle='--', which='both', alpha=0.6)

    ax.step(time_steps, value1, where="post", label='heat_water_tes_tp_val_hw',
            linestyle='-', color='r', linewidth=2, alpha=0.7)
    ax.step(time_steps, value2, where="post", label='heat_tp_val_hw_e_boi',
            linestyle='-', color='b', linewidth=2, alpha=0.7)
    ax.step(time_steps, value3, where="post", label='input_elec_e_boi',
            linestyle='-', color='g', linewidth=2, alpha=0.7)

    plt.legend(loc='best', prop=font_legend)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(value1), max(value2), max(value3)) * 1.5)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_hw_cns(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld,
                               'hw_cns')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data2 = df[df['var'].str.contains('heat_water_tes_tp_val_hw')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('input_heat_hw_cns')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']


    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    ax.set_ylim(ymin=0,  ymax=180)
    ax.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Diagramm des Solarspeichers', font_titel, y=1.02)

    ax.step(time_steps, value2, where="post", label='heat_water_tes_tp_val', zorder=20,
                    color='r', linewidth=1.5, alpha=0.5)
    #ax.fill_between(time_steps, value2, 0, facecolor='r', label='heat_water_tes_tp_val',
                    #zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, value3, where="post",
                    color='b', linewidth=0.1, alpha=0.5)
    ax.fill_between(time_steps, value3, 0, facecolor='b', label='input_heat_hw_cns',
                    zorder=10, step="post", alpha=0.5)
    ax.set_ylim(ymin=0)

    plt.legend(loc='best', prop=font_legend)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_hw(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'e_boi')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('temp_water_tes')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('output_heat_boi_s')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']
    data3 = df[df['var'].str.contains('input_heat_hw_cns')]
    data3 = data3.reset_index(drop=True)
    value3 = data3['value']

    data7 = df[df['var'].str.contains('size_water_tes')]
    data7 = data7.reset_index(drop=True)
    data7 = data7['value']
    value7 = data7[0]
    value8 = 4180 * value7 * (value1 - 40)/3600
    value5 = value8 + value2

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Stromerzeugung', font_titel, y=1.02)
    ax.step(time_steps, value3, where="post", label='Strom Eigenerzeugung',
            linestyle='-', color='k', linewidth=1, zorder=20)

    ax.step(time_steps, value8, where="post",
            linestyle='-', color='r', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value8, 0, facecolor='r', label='gespeicherte Energie im Speicher',
                    zorder=10, step="post", alpha=0.5)

    ax.step(time_steps, value5, where="post",
            linestyle='-', color='b', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value5, value8, facecolor='b', label='Energie aus HK',
                    zorder=10, step="post", alpha=0.5)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.legend(loc='best', prop=font_legend)
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_hw(csv_file, time_step, bld):
    font_label = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'e_boi')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[df['var'].str.contains('input_heat_e_boi')]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[df['var'].str.contains('heat_water_tes_tp_val_hw')]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']

    value3=value2+value1


    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    #ax.set_title('Stromerzeugung', font_titel, y=1.02)


    ax.step(time_steps, value2, where="post",
            linestyle='-', color='r', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value2, 0, facecolor='r', label='input_heat_e_boi',
                    zorder=10, step="post", alpha=0.5)

    ax.step(time_steps, value2, where="post",
            linestyle='-', color='b', linewidth=0.1, zorder=10)
    ax.fill_between(time_steps, value3, value2, facecolor='b', label='heat_water_tes_tp_val_hw',
                    zorder=10, step="post", alpha=0.5)

    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r"Leistung (kW)", font_label)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.legend(loc='best', prop=font_legend)
    fig.tight_layout()

    plt.savefig(plot_output)

def step_plot_elec_ein_aus(csv_file, time_step, bld, n=1.1):
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '14'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '14'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '17'}
    plot_output = os.path.join(opt_output_path, 'plot', bld, 'Energieaustausch des Netzes')
    df = pd.read_csv(csv_file)
    time_steps = range(time_step)

    data1 = df[(df['var'].str.contains('input_elec_e_grid'))]
    data1 = data1.reset_index(drop=True)
    value1 = data1['value']
    data2 = df[(df['var'].str.contains('output_elec_e_grid'))]
    data2 = data2.reset_index(drop=True)
    value2 = data2['value']

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(4))
    ax.xaxis.set_major_locator(MultipleLocator(24))
    plt.grid(linestyle='--', which='both')

    ax.step(time_steps, value1,  where="post", linestyle='-',
            color='r', linewidth=0.1)
    ax.fill_between(time_steps, value1, 0, facecolor='r', label='Netz Input',
                    zorder=10, step="post", alpha=0.5)
    ax.step(time_steps, value2,  where="post", linestyle='-',
            color='b', linewidth=0.1)
    ax.fill_between(time_steps, value2, 0, facecolor='b', label='Netz Output',
                    zorder=10, step="post", alpha=0.5)

    plt.legend(loc='best', prop=font_legend)
    #ax.set_title(titel, font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel(r'Leistung (kW)', font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(value1), max(value2)) * n)
    # ax.tick_params(labelsize=12)
    plt.xticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=14, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)