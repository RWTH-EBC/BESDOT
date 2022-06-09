import os
import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MultipleLocator
from scripts.Environment import Environment

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def step_plot_one_line(von, bis, nr, n=1.1, legend_pos='best'):
    result_output_path = os.path.join(base_path, 'data', 'cls_file', str(nr) + 'day_24hour.csv')
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '15'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '15'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '18'}

    plot_output = os.path.join(base_path, 'data', 'cls_file', 'Wärmebedarf_' + str(nr))

    df = pd.read_csv(result_output_path)
    time_steps = range(von, bis + 1)

    data1 = df.iloc[von:bis + 1, 4]
    data1 = data1.reset_index(drop=True)

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(5))
    ax.grid(linestyle='--', which='both', alpha=0.6)

    ax.step(time_steps, data1, where="post", label='heat_demand',
            linestyle='-', color='r', linewidth=2, alpha=0.7)

    plt.legend(loc=legend_pos, prop=font_legend)
    ax.set_title('Bedarf', font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel('Leistung (kW)', font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(data1) * n)
    plt.xticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


def step_plot_three_lines(von, bis, nr, n=1.1, legend_pos='best'):
    result_output_path = os.path.join(base_path, 'data', 'cls_file', str(nr) + 'day_24hour.csv')
    font_label = {'family': 'Times New Roman', 'weight': 'semibold', 'style':
        'normal', 'size': '15'}
    font_legend = {'family': 'Times New Roman', 'weight': 'medium', 'style':
        'normal', 'size': '15'}
    font_titel = {'family': 'Times New Roman', 'weight': 'bold', 'style':
        'normal', 'size': '18'}
    plot_output = os.path.join(base_path, 'data', 'cls_file', 'Bedarf_' + str(nr))

    df = pd.read_csv(result_output_path)
    time_steps = range(von, bis + 1)

    data1 = df.iloc[von:bis + 1, 4]
    data1 = data1.reset_index(drop=True)
    data2 = df.iloc[von:bis + 1, 5]
    data2 = data2.reset_index(drop=True)
    data3 = df.iloc[von:bis + 1, 3]
    data3 = data3.reset_index(drop=True)

    fig = plt.figure(figsize=(6.5, 5.5))
    ax = fig.add_subplot(111)
    ax.xaxis.set_minor_locator(MultipleLocator(5))
    ax.grid(linestyle='--', which='both', alpha=0.6)

    ax.step(time_steps, data1, where="post", label='heat_demand',
            linestyle='-', color='r', linewidth=2, alpha=0.7)
    ax.step(time_steps, data2, where="post", label='hot_water_demand',
            linestyle='-', color='b', linewidth=2, alpha=0.7)
    ax.step(time_steps, data3, where="post", label='elec_demand',
            linestyle='-', color='g', linewidth=2, alpha=0.7)

    plt.legend(loc=legend_pos, prop=font_legend)
    ax.set_title('Bedarf', font_titel, y=1.02)
    ax.set_xlabel("Stunde (h)", font_label)
    ax.set_ylabel('Leistung (kW)', font_label)
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymax=max(max(data1), max(data2), max(data3)) * n)
    plt.xticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    plt.yticks(fontname='Times New Roman', fontsize=15, fontweight='medium')
    fig.tight_layout()

    plt.savefig(plot_output)


step_plot_one_line(von=0, bis=13 * 24-1, nr=12)
step_plot_three_lines(von=0, bis=13 * 24-1, nr=12)
