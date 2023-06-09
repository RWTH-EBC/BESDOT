"""

EHDO - ENERGY HUB DESIGN OPTIMIZATION Tool

Developed by:   E.ON Energy Research Center,
                Institute for Energy Efficient Buildings and Indoor Climate,
                RWTH Aachen University,
                Germany

Contact:        Marco Wirtz
                marco.wirtz@eonerc.rwth-aachen.de

                k_mediods clustering implemented by Thomas Schütz (2015).
"""

from __future__ import division
import os
import warnings
import numpy as np
import pandas as pd
import math
import cluster.k_medoids as k_medoids

# import optimizer.load_params as load_params


BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _distances(values, norm=2):
    """
    Compute distance matrix for all data sets (rows of values)

    Parameters
    ----------
    values : 2-dimensional array
        Rows represent days and columns values
    norm : integer, optional
        Compute the distance according to this norm. 2 is the standard
        Euklidean-norm.

    Return
    ------
    d : 2-dimensional array
        Distances between each data set
    """
    # Initialize distance matrix
    d = np.zeros((values.shape[1], values.shape[1]))

    # Define a function that computes the distance between two days
    dist = (lambda day1, day2, r:
            math.pow(np.sum(np.power(np.abs(day1 - day2), r)), 1 / r))

    # Remember: The d matrix is symmetrical!
    for i in range(values.shape[1]):  # loop over first days
        for j in range(i + 1, values.shape[1]):  # loop second days
            d[i, j] = dist(values[:, i], values[:, j], norm)

    # Fill the remaining entries
    d = d + d.T

    return d


def cluster(inputs, number_clusters=12, norm=2, time_limit=300, mip_gap=0.0,
            weights=None):
    """
    Cluster a set of inputs into clusters by solving a k-medoid problem.

    Parameters
    ----------
    inputs : 2-dimensional array
        First dimension: Number of different input types.
        Second dimension: Values for each time step of interes.
    number_clusters : integer, optional
        How many clusters shall be computed?
    norm : integer, optional
        Compute the distance according to this norm. 2 is the standard
        Euklidean-norm.
    time_limit : integer, optional
        Time limit for the optimization in seconds
    mip_gap : float, optional
        Optimality tolerance (0: proven global optimum)
    weights : 1-dimensional array, optional
        Weight for each input. If not provided, all inputs are treated equally.

    Returns
    -------
    scaled_typ_days :
        Scaled typical demand days. The scaling is based on the annual demands.
    nc : array_like
        Weighting factors of each cluster
    z : 2-dimensional array
        Mapping of each day to the clusters
    """
    # Determine time steps per day
    # print(inputs)
    # print(inputs.shape[0])
    print(inputs.shape[1])
    len_day = int(inputs.shape[1] / 365)
    # len_day = int(inputs.shape[0] / 365)

    # Set weights if not already given
    if weights == None:
        weights = np.ones(inputs.shape[0])
    elif not sum(weights) == 1:  # Rescale weights
        weights = np.array(weights) / sum(weights)

    # Manipulate inputs
    # Initialize arrays
    inputsTransformed = []
    inputsScaled = []
    inputsScaledTransformed = []

    # Fill and reshape
    # Scaling to values between 0 and 1, thus all inputs shall have the same
    # weight and will be clustered equally in terms of quality
    for i in range(inputs.shape[0]):
        vals = inputs[i, :]
        if np.max(vals) == np.min(vals):
            temp = np.zeros_like(vals)
        else:
            print(np.min(vals))
            print(np.max(vals))
            temp = ((vals - np.min(vals)) / (np.max(vals) - np.min(vals))
                    * math.sqrt(weights[i]))
        inputsScaled.append(temp)
        inputsScaledTransformed.append(temp.reshape((len_day, 365), order="F"))
        inputsTransformed.append(vals.reshape((len_day, 365), order="F"))

    # Put the scaled and reshaped inputs together
    L = np.concatenate(tuple(inputsScaledTransformed))

    # Compute distances
    d = _distances(L, norm)

    # Execute optimization model
    (y, z, obj) = k_medoids.k_medoids(d,
                                      number_clusters,
                                      time_limit,
                                      mip_gap)

    # Section 2.3 and retain typical days
    nc = np.zeros_like(y)
    typicalDays = []

    # nc contains how many days are there in each cluster
    nc = []
    for i in range(len(y)):
        temp = np.sum(z[i, :])
        if temp > 0:
            nc.append(temp)
            typicalDays.append([ins[:, i] for ins in inputsTransformed])

    typicalDays = np.array(typicalDays)
    nc = np.array(nc, dtype="int")
    nc_cumsum = np.cumsum(nc) * len_day

    # Construct (yearly) load curves
    # ub = upper bound, lb = lower bound
    clustered = np.zeros_like(inputs)
    for i in range(len(nc)):
        if i == 0:
            lb = 0
        else:
            lb = nc_cumsum[i - 1]
        ub = nc_cumsum[i]

        for j in range(len(inputsTransformed)):
            clustered[j, lb:ub] = np.tile(typicalDays[i][j], nc[i])

    # Scaling to preserve original demands
    sums_inputs = [np.sum(inputs[j, :]) for j in range(inputs.shape[0])]
    scaled = np.array([nc[day] * typicalDays[day, :, :]
                       for day in range(number_clusters)])
    sums_scaled = [
        np.sum(scaled[:, j, :]) if not np.sum(scaled[:, j, :]) == 0 else 1
        for j in range(inputs.shape[0])]
    scaling_factors = [sums_inputs[j] / sums_scaled[j]
                       for j in range(inputs.shape[0])]
    scaled_typ_days = [scaling_factors[j] * typicalDays[:, j, :]
                       for j in range(inputs.shape[0])]

    return scaled_typ_days, nc, z


def medoids_weather_opt(district, scenario, grid_typ):
    """Optimization of the typical buildings with MILP solver"""
    # Set the path variables, including output path
    output_dir_path = os.path.join(BASE_PATH, 'outputs', 'clustering',
                                   'weather_cluster',
                                   district + '_' + scenario +
                                   '_' + grid_typ)
    if not os.path.isdir(output_dir_path):
        os.mkdir(output_dir_path)

    # read cluster results, find out all medoids, add medoids into a list.
    medoids_list = []
    clustering_dir = os.path.join(BASE_PATH, 'outputs', 'clustering')
    cluster_results_dir_name = 'cluster_res_20201102'
    cluster_results_dir = os.path.join(clustering_dir, cluster_results_dir_name)
    for _files in os.listdir(clustering_dir):
        if os.path.isdir(os.path.join(clustering_dir, _files)):
            if 'cluster_res_' in _files and \
                    _files is not cluster_results_dir_name:
                if int(_files[-8:]) > int(cluster_results_dir_name[-8:]):
                    warnings.warn("Atention! The clustering result is not the "
                                  "latest one. Current is the " +
                                  cluster_results_dir_name + " used, and there"
                                                             " is " + _files)

    res_cluster_result_file = os.path.join(cluster_results_dir, district + "_" +
                                           scenario + "_" + grid_typ +
                                           "_resident.csv")
    nonres_cluster_result_file = os.path.join(cluster_results_dir, district +
                                              "_" + scenario + "_" + grid_typ +
                                              "_nonresident.csv")
    res_cluster_result = pd.read_csv(res_cluster_result_file)
    medoids_list += list(set(res_cluster_result['medoid'].values.tolist()))
    non_cluster_result = pd.read_csv(nonres_cluster_result_file)
    medoids_list += list(set(non_cluster_result['medoid'].values.tolist()))

    # get the electricity and heat demand of medoid.
    if district == 'Dusseldorf':
        if scenario == 'ist':
            scenario_dir = 'Düsseldorf_IST'
            weather_data = os.path.join(BASE_PATH, 'inputs', 'weather_data',
                                        'Dusseldorf_Wetterdaten_DWD',
                                        'TRY2015_511803068371_Jahr.dat')
        else:
            scenario_dir = 'Düsseldorf_2050'
            weather_data = os.path.join(BASE_PATH, 'inputs', 'weather_data',
                                        'Dusseldorf_Wetterdaten_DWD',
                                        'TRY2045_511803068371_Jahr.dat')
    else:
        if scenario == 'ist':
            scenario_dir = district + '_IST'
            if district == 'Langenau':
                weather_data = os.path.join(BASE_PATH, 'inputs', 'weather_data',
                                            district + '_Wetterdaten_DWD',
                                            'TRY2015_508415132871_Jahr.dat')
            else:
                weather_data = os.path.join(BASE_PATH, 'inputs', 'weather_data',
                                            district + '_Wetterdaten_DWD',
                                            'TRY2015_476023098831_Jahr.dat')
        else:
            scenario_dir = district + '_2050'
            if district == 'Langenau':
                weather_data = os.path.join(BASE_PATH, 'inputs', 'weather_data',
                                            district + '_Wetterdaten_DWD',
                                            'TRY2045_508415132871_Jahr.dat')
            else:
                weather_data = os.path.join(BASE_PATH, 'inputs', 'weather_data',
                                            district + '_Wetterdaten_DWD',
                                            'TRY2045_476023098831_Jahr.dat')

    if scenario == "ist":
        weather_profile = pd.read_table(weather_data, skiprows=33, sep='\t')
    elif scenario in ["2050_nitsche", "2050_10g", "2050_95"]:
        weather_profile = pd.read_table(weather_data, skiprows=35, sep='\t')
    temperature_profile = weather_profile.iloc[:, 0].str.split('\s+',
                                                               17).str[
        5].astype('float64').values
    wind_profile = weather_profile.iloc[:, 0].str.split('\s+', 17).str[
        8].astype('float64').values
    direct_solar_profile = weather_profile.iloc[:, 0].str.split('\s+', 17).str[
        12].astype('float64').values
    diffuse_solar_profile = weather_profile.iloc[:, 0].str.split('\s+', 17).str[
        13].astype('float64').values
    total_solar_profile = diffuse_solar_profile + direct_solar_profile

    for medoid in medoids_list:
        medoid_heat_file = os.path.join(BASE_PATH, 'outputs', 'demgen',
                                        scenario_dir, medoid + '.csv')
        medoid_elec_file = os.path.join(BASE_PATH, 'outputs',
                                        'standardlastprofil', scenario_dir,
                                        medoid + '.csv')
        medoid_heat = np.loadtxt(medoid_heat_file, delimiter=",")
        medoid_elec = np.loadtxt(medoid_elec_file, delimiter=",")[0:8760]

        # set the parameters for optimzation
        output_path = os.path.join(output_dir_path, str(medoid) + '.csv')

        all_models = gen_all_model(medoid_heat, medoid_elec, district,
                                   decent=True)
        price_dict = get_price_dict(scenario)

        param = {}
        param_uncl = {}
        dem_uncl = {}
        param_uncl["T_air"] = temperature_profile
        param_uncl["GHI"] = total_solar_profile
        param_uncl["wind_speed"] = wind_profile
        name_dict = {"HeatDemand": "heat", "CoolDemand": "cool",
                     "PowerDemand": "power", "H2Demand": "hydrogen"}
        for k in name_dict.keys():
            try:
                dem_uncl[name_dict[k]] = all_models[k]  # kW
            except:
                pass
        for k in name_dict.keys():
            param["peak_" + name_dict[k]] = np.max(dem_uncl[name_dict[k]])
        param["n_clusters"] = 12

        time_series = [dem_uncl["heat"], dem_uncl["cool"], dem_uncl["power"],
                       dem_uncl["hydrogen"], param_uncl["T_air"],
                       param_uncl["GHI"], param_uncl["wind_speed"]]
        # Only the building demands are clustered using k-medoids algorithm; secondary time series are clustered manually according to k-medoids result
        inputs_clustering = np.array(time_series)

        print("Cluster design days...")
        (clustered_series, nc, z) = cluster(inputs_clustering,
                                            param["n_clusters"],
                                            norm=2,
                                            mip_gap=0.02,
                                            )

        print(clustered_series)
        print(nc)
        print(z)
        pd.DataFrame(np.array(nc)).to_csv(output_path, header=None)


def gen_all_model(heat_demand, elec_demand, district, decent=False):
    cool_demand_list = [0] * 8760
    cool_demand = np.array(cool_demand_list, dtype='float64')
    gas_demand_list = [0] * 8760
    gas_demand = np.array(gas_demand_list, dtype='float64')

    if not decent:
        if district == "Dusseldorf":
            all_models = {"HeatDemand": heat_demand, "CoolDemand": cool_demand,
                          "PowerDemand": elec_demand, "H2Demand": gas_demand,
                          "Photovoltaic": True, "WindTurbine": False,
                          "Hydropower": False, "SolarThermalCollector": False,
                          "CHP": True, "GasBoiler": True, "GasHeatPump": False,
                          "HeatPump": True, "ElectricBoiler": True,
                          "CompressionChiller": True, "AbsorptionChiller": True,
                          "BiomassCHP": False, "BiomassBoiler": False,
                          "WasteCHP": False, "WasteBoiler": False,
                          "Electrolyzer": False, "FuelCell": True,
                          "H2Storage": False, "SabatierReactor": False,
                          "HeatStorage": True, "ColdStorage": True,
                          "Battery": True,
                          "GasStorage": False, "enable_price_cap_el": False,
                          "enable_feed_in_el": True,
                          "enable_cap_limit_el": False,
                          "enable_supply_limit_el": False,
                          "enable_price_cap_gas": False,
                          "enable_feed_in_gas": False,
                          "enable_cap_limit_gas": False,
                          "enable_supply_limit_gas": False,
                          "enable_supply_limit_biomass": False,
                          "enable_supply_limit_hydrogen": False,
                          "enable_supply_limit_waste": False,
                          "ReferenceCase": False,
                          "enable_ref_chp": False}
        elif district in ["Langenau", "Lindenberg"]:
            all_models = {"HeatDemand": heat_demand, "CoolDemand": cool_demand,
                          "PowerDemand": elec_demand, "H2Demand": gas_demand,
                          "Photovoltaic": True, "WindTurbine": True,
                          "Hydropower": False, "SolarThermalCollector": False,
                          "CHP": True, "GasBoiler": True, "GasHeatPump": False,
                          "HeatPump": True, "ElectricBoiler": True,
                          "CompressionChiller": True, "AbsorptionChiller": True,
                          "BiomassCHP": True, "BiomassBoiler": True,
                          "WasteCHP": False, "WasteBoiler": False,
                          "Electrolyzer": False, "FuelCell": True,
                          "H2Storage": False, "SabatierReactor": False,
                          "HeatStorage": True, "ColdStorage": True,
                          "Battery": True,
                          "GasStorage": False, "enable_price_cap_el": False,
                          "enable_feed_in_el": True,
                          "enable_cap_limit_el": False,
                          "enable_supply_limit_el": False,
                          "enable_price_cap_gas": False,
                          "enable_feed_in_gas": False,
                          "enable_cap_limit_gas": False,
                          "enable_supply_limit_gas": False,
                          "enable_supply_limit_biomass": False,
                          "enable_supply_limit_hydrogen": False,
                          "enable_supply_limit_waste": False,
                          "ReferenceCase": False,
                          "enable_ref_chp": False}
    else:
        all_models = {"HeatDemand": heat_demand, "CoolDemand": cool_demand,
                      "PowerDemand": elec_demand, "H2Demand": gas_demand,
                      "Photovoltaic": True, "WindTurbine": False,
                      "Hydropower": False, "SolarThermalCollector": True,
                      "CHP": True, "GasBoiler": True, "GasHeatPump": False,
                      "HeatPump": True, "ElectricBoiler": True,
                      "CompressionChiller": True, "AbsorptionChiller": True,
                      "BiomassCHP": False, "BiomassBoiler": False,
                      "WasteCHP": False, "WasteBoiler": False,
                      "Electrolyzer": False, "FuelCell": True,
                      "H2Storage": False, "SabatierReactor": False,
                      "HeatStorage": True, "ColdStorage": True, "Battery": True,
                      "GasStorage": False, "enable_price_cap_el": False,
                      "enable_feed_in_el": True, "enable_cap_limit_el": False,
                      "enable_supply_limit_el": False,
                      "enable_price_cap_gas": False,
                      "enable_feed_in_gas": False,
                      "enable_cap_limit_gas": False,
                      "enable_supply_limit_gas": False,
                      "enable_supply_limit_biomass": False,
                      "enable_supply_limit_hydrogen": False,
                      "enable_supply_limit_waste": False,
                      "ReferenceCase": False,
                      "enable_ref_chp": False}
    return all_models


def get_price_dict(scenario):
    """This function contains the price and co2 factors for different
    scenarios"""
    price_dict = {}

    if scenario == "ist":
        price_dict["gas_price"] = 0.0427  # unit cent/kWh
        price_dict["elec_price"] = 0.2608  # unit cent/kWh
        price_dict["elec_feed_price"] = 0.0987  # unit cent/kWh from 01.01.2020
        price_dict["co2_price"] = 25  # unit €/t
        price_dict["gas_factor"] = 202  # g/kWh
        price_dict["elec_factor"] = 400  # g/kWh
    elif scenario == "2050_nitsche":
        price_dict["gas_price"] = 0.0487  # unit cent/kWh
        price_dict["elec_price"] = 0.2461  # unit cent/kWh
        price_dict["elec_feed_price"] = 0.0987  # unit cent/kWh from 01.01.2020
        price_dict["co2_price"] = 180  # unit €/t
        price_dict["gas_factor"] = 109  # g/kWh
        price_dict["elec_factor"] = 8  # g/kWh
    elif scenario == "2050_10g":
        price_dict["gas_price"] = 0.0487  # unit cent/kWh
        price_dict["elec_price"] = 0.2461  # unit cent/kWh
        price_dict["elec_feed_price"] = 0.0987  # unit cent/kWh from 01.01.2020
        price_dict["co2_price"] = 180  # unit €/t
        price_dict["gas_factor"] = 10  # g/kWh
        price_dict["elec_factor"] = 10  # g/kWh
    elif scenario == "2050_95":
        price_dict["gas_price"] = 0.0487  # unit cent/kWh
        price_dict["elec_price"] = 0.2461  # unit cent/kWh
        price_dict["elec_feed_price"] = 0.0987  # unit cent/kWh from 01.01.2020
        price_dict["co2_price"] = 180  # unit €/t
        price_dict["gas_factor"] = 10.2  # g/kWh
        price_dict["elec_factor"] = 38.2  # g/kWh

    return price_dict


if __name__ == '__main__':
    for district in ["Dusseldorf"]:
        for scenario in ["ist"]:
            for grid_typ in ["500kWh", "1500kWh", "3000kWh", "6000kWh"]:
                medoids_weather_opt(district=district, scenario=scenario,
                                    grid_typ=grid_typ)
