# -*- coding: utf-8 -*-
# @Author: mma
# @Date:   2022-01-14 15:27:55
# @Last Modified by:   mma
# @Last Modified time: 2022-01-17 16:29:53
import collections
import datetime
import json
import multiprocessing
import os
import sys
import warnings

import numpy as np
import pandas as pd

sys.path.insert(
    0,
    os.path.join(
        "C:\\",
        "Program Files",
        "Dymola 2021",
        "Modelica",
        "Library",
        "python_interface",
        "dymola.egg",
    ),
)

from shapely.geometry import Polygon
from teaser.data.dataclass import DataClass
from teaser.logic.archetypebuildings.nonresidential import NonResidential
from teaser.logic.archetypebuildings.residential import Residential
from teaser.logic.buildingobjects.buildingphysics.window import Window
from teaser.project import Project

import utils.read_results as res

# helper scripts
import utils.simulate as sim
from utils.read_results import compact_results
from utils.utils import (
    get_orientation,
    latlon2abs,
    poly_to_multiline,
    random_choice,
    set_json_info,
)

warnings.simplefilter(action="ignore", category=FutureWarning)

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import gridspec
from matplotlib.collections import LineCollection
from matplotlib.pylab import mpl

# plt.style.use("~/ebc.paper.mplstyle")
plt.style.use("ebc.paper.mplstyle")

rwth_colors_dict = {
    "black_100": "#000000",
    "black_75": "#646567",
    "black_50": "#9C9EA9",
    "blue_100": "#00549F",
    "blue_75": "#407FB7",
    "blue_50": "#8EBAE5",
    "blue_25": "#C7DDF2",
    "blue_10": "#E8F1FA",
    "red_100": "#CC071E",
    "red_75": "#D85C41",
    "red_50": "#E69679",
    "orange_100": "#F6A800",
    "orange_75": "#FABE50",
    "orange_50": "#FDD48F",
    "green_100": "#57AB27",
    "green_75": "#8DC060",
    "green_50": "#B8D698",
    "magenta_100": "#E30066",
    "magenta_75": "#E96088",
    "magenta_50": "#F19EB1",
    "petrol_100": "#006165",
    "petrol_75": "#2D7F83",
    "petrol_50": "#7DA4A7",
    "violett_100": "#612156",
    "violett_75": "#834E75",
    "violett_50": "#D2C0CD",
}


class MidpointNormalize(matplotlib.colors.Normalize):
    def __init__(self, vmin=None, vmax=None, vcenter=None, clip=False):
        self.vcenter = vcenter
        super().__init__(vmin, vmax, clip)

    def __call__(self, value, clip=None):
        # I'm ignoring masked values and all kinds of edge cases to make a
        # simple example...
        x, y = [self.vmin, self.vcenter, self.vmax], [0, 0.5, 1]
        return np.ma.masked_array(np.interp(value, x, y))


def plot_heatmap_df(data, name, cmap_str):

    # 3600s
    data = data.resample("H").mean()
    index = np.arange(0, 8760 * 3600, 3600)

    # routine after setting index

    data.index = index

    test = []
    if len(data.index) == 8760:
        for index, val in enumerate(data):
            if index != 0 and index % 24 == 0:
                test.append(data[index - (23) : index].values)
    else:
        for index, val in enumerate(data):
            if index != 0 and index % 96 == 0:
                test.append(data[index - (95) : index].values)

    test = np.array(test)

    # plot and save for input overview

    fig1, ax11 = plt.subplots()

    # fig1.suptitle("Demands Freiburg", fontsize=5)

    # define cmap and normalize to zero
    cmap = sns.color_palette(cmap_str, as_cmap=True)
    plot = ax11.pcolor(test.T, cmap=cmap)

    if test.min().min() == 0.0 or test.max().max() == 0.0:
        center = (test.max().max() - test.min().min()) / 2
    else:
        center = 0

    midnorm = MidpointNormalize(
        vmin=test.min().min(), vcenter=center, vmax=test.max().max()
    )

    pc = ax11.pcolormesh(test.T, rasterized=True, norm=midnorm, cmap=cmap)

    cbar = fig1.colorbar(pc, orientation="vertical", shrink=0.9, pad=0.03, aspect=15)

    # get min max lables
    min_n = int(data.min().min())
    if min_n % 2:
        pass
    else:
        min_n += 1
    max_n = int(data.max().max())
    if max_n % 2:
        pass
    else:
        max_n += 1

    cbar.ax.set_yticklabels([str(int(i)) + " kW" for i in cbar.get_ticks()])
    if len(data.index) == 8760:
        plt.yticks([0, 6, 12, 18, 24])
    else:
        plt.yticks([0, 6 * 4, 12 * 4, 18 * 4, 24 * 4], [0, 6, 12, 18, 24])
    ax11.set_ylabel(r"Tageszeit")
    ax11.set_xlabel(r"Zeit in Tagen")

    fig1.savefig(output_path.replace("plt", name))


def plot_demands(heat_csv_path, cool_csv_path, output_path):

    sns.set()
    sns.set_context("paper")
    sns.set_style("ticks")

    # title = "Wärme- und Kältebedarf in kW"
    title = "Wärmebedarf"
    # title = "Wärmebedarf in kW"

    data = pd.DataFrame(
        index=pd.date_range(
            start=datetime.datetime(2021, 1, 1, 0, 0, 0),
            end=datetime.datetime(2021, 12, 31, 23, 00),
            freq="15min",
        ),
        # columns=["Wärmeleistung", "Kälteleistung"],
        columns=["Wärmeleistung"],
    )
    data["Wärmeleistung"] = (
        pd.read_csv(heat_csv_path, sep=";", index_col=0).sum(axis=1).values / 1000
    )
    # data["Kälteleistung"] = (
    #     -pd.read_csv(cool_csv_path, sep=";", index_col=0).sum(axis=1).values / 1000
    # )

    sitewidth = 6.224
    fontsize = 11
    font = {"family": "serif", "weight": "normal", "size": fontsize}
    params = {
        "legend.fontsize": fontsize,
        "xtick.labelsize": fontsize,
        "ytick.labelsize": fontsize,
        "axes.labelsize": fontsize,
        "axes.titlesize": fontsize,
    }
    matplotlib.rc("font", **font)
    # demand
    fig = plt.figure("Demand", figsize=(sitewidth, sitewidth / 16 * 9))
    # matplotlib.rcParams.update(params)
    ax = sns.lineplot(
        data=data,
        # palette=[rwth_colors_dict["red_75"], rwth_colors_dict["blue_75"]],
        palette=[rwth_colors_dict["red_75"]],
        linewidth=1.5,
    )
    ax.set_ylabel("Leistung in kW")
    ax.set_xlabel("Datum")
    ax.set_ylim([data.min().min() * 1.1, data.max().max() * 1.1])
    ax.set_xlim([data.index[0], data.index[-1] + pd.Timedelta(1, unit="h")])
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%y"))

    plt.title(title)
    plt.savefig(output_path, dpi=200)
    plt.clf()
    ax = sns.lineplot(
        data=data.resample("D").mean(),
        # hue={"ls": ["-", "--"]},
        palette=[rwth_colors_dict["red_75"]],
        linewidth=1.5,
    )
    ax.set_ylabel("Leistung in kW")
    ax.set_xlabel("Datum")
    ax.set_ylim(
        [
            data.resample("D").mean().min().min() * 1.1,
            data.resample("D").mean().max().max() * 1.1,
        ]
    )
    ax.set_xlim([data.index[0], data.index[-1] + pd.Timedelta(1, unit="h")])
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%y"))
    plt.title(title + " D")
    plt.tight_layout()
    plt.savefig(output_path.replace("plt", "plt_D"), dpi=200)
    plt.clf()
    ax = sns.lineplot(
        data=data.resample("1h").mean(),
        # hue={"ls": ["-", "--"]},
        # palette=[rwth_colors_dict["red_75"], rwth_colors_dict["blue_75"]],
        palette=[rwth_colors_dict["red_75"]],
        linewidth=1.5,
    )
    ax.set_ylabel("Leistung in kW")
    ax.set_xlabel("Datum")
    ax.set_ylim(
        [
            data.resample("1h").mean().min().min() * 1.1,
            data.resample("1h").mean().max().max() * 1.1,
        ]
    )
    ax.set_xlim([data.index[0], data.index[-1] + pd.Timedelta(1, unit="h")])
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%y"))
    plt.title(title + " 1h")
    plt.tight_layout()
    plt.savefig(output_path.replace("plt", "plt_1h"), dpi=200)
    plt.clf()

    # DOC useless! Zero here!

    # data["Kälteleistung"] = -data["Kälteleistung"]
    data["DOC"] = data.min(axis=1)

    # Plot Heatmaps

    # create dataframe with residual heat and cool
    # 900s
    df_heating = data["Wärmeleistung"]
    # df_cooling = data["Kälteleistung"]

    plot_heatmap_df(df_heating, "heatmap_heating", "Reds")
    # plot_heatmap_df(df_cooling, "heatmap_cooling", "Blues")
    # plot_heatmap_df(df_heating - df_cooling, "heatmap_heating_cooling", "vlag")


if __name__ == "__main__":
    DIR_SCRIPT = os.path.abspath(os.path.dirname(__file__))
    DIR_TOP = os.path.abspath(DIR_SCRIPT)
    RESULTS_PATH = os.path.join(DIR_TOP, "results")
    sim_random_name = "kshd"
    index = pd.date_range(datetime.datetime(2020, 1, 1), periods=35037, freq="15min")

    # with_tempdrop = True
    with_tempdrop = False
    analyse = dict()
    conditions = ["ref", "summer", "winter"]
    for type in conditions:
        analyse[type] = dict()
        if with_tempdrop:
            analyse[type]["name"] = type
        else:
            analyse[type]["name"] = type + "_notempdrop"

    # # get all construction sites and filenames
    # path = os.path.join(DIR_SCRIPT, "freiburg", "bldg_inputs")
    # list_of_construction_sites = []
    # for root, dirs, files in os.walk(path):
    #     for file in files:
    #         if file.startswith("buildings_Freiburg"):
    #             list_of_construction_sites.append(os.path.join(root, file))

    for condition in analyse:
        prj = Project(load_data=True)
        prj.name = "Freiburg_{}_{}".format(sim_random_name, analyse[condition]["name"])
        heat_csv_path = os.path.join(
            RESULTS_PATH, prj.name, prj.name + "_heat_results.csv"
        )
        cool_csv_path = os.path.join(
            RESULTS_PATH, prj.name, prj.name + "_cool_results.csv"
        )
        output_path = os.path.join(
            RESULTS_PATH, prj.name, prj.name + "_heat_cool_plt.pdf"
        )

        plot_demands(heat_csv_path, cool_csv_path, output_path)
    # ##
    # prj = Project(load_data=True)
    # prj.name = "Freiburg_{}_{}".format(sim_random_name, "ref")
    # heat_csv_path = os.path.join(RESULTS_PATH, prj.name, prj.name + "_heat_results.csv")
    # cool_csv_path = os.path.join(RESULTS_PATH, prj.name, prj.name + "_cool_results.csv")
    # output_path = os.path.join(RESULTS_PATH, prj.name, prj.name + "_heat_cool_plt.pdf")

    # plot_demands(heat_csv_path, cool_csv_path, output_path)

    # ###
    # prj = Project(load_data=True)
    # prj.name = "Freiburg_{}_{}".format(sim_random_name, "summer")
    # heat_csv_path = os.path.join(RESULTS_PATH, prj.name, prj.name + "_heat_results.csv")
    # cool_csv_path = os.path.join(RESULTS_PATH, prj.name, prj.name + "_cool_results.csv")
    # output_path = os.path.join(RESULTS_PATH, prj.name, prj.name + "_heat_cool_plt.pdf")

    # plot_demands(heat_csv_path, cool_csv_path, output_path)

    # ###
    # prj = Project(load_data=True)
    # prj.name = "Freiburg_{}_{}".format(sim_random_name, "winter")
    # heat_csv_path = os.path.join(RESULTS_PATH, prj.name, prj.name + "_heat_results.csv")
    # cool_csv_path = os.path.join(RESULTS_PATH, prj.name, prj.name + "_cool_results.csv")
    # output_path = os.path.join(RESULTS_PATH, prj.name, prj.name + "_heat_cool_plt.pdf")

    # plot_demands(heat_csv_path, cool_csv_path, output_path)

