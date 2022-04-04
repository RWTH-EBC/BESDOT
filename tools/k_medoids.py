"""
Adjust the k medoids tool from EHDO (ENERGY HUB DESIGN OPTIMIZATION Tool)
with pyomo.
Original code comes from k_mediods clustering implemented by Thomas Schütz (
2015).
"""
import os
import warnings
import math
import pyomo.environ as pyo
# import gurobipy as gp
import numpy as np
import pandas as pd
from sklearn.cluster import KMedoids


# Implementation of the k-medoids problem, as it is applied in
# Selection of typical demand days for CHP optimization
# Fernando Domínguez-Muñoz, José M. Cejudo-López, Antonio Carrillo-Andrés and
# Manuel Gallardo-Salazar
# Energy and Buildings. Vol 43, Issue 11 (November 2011), pp. 3036-3043

# Original formulation (hereafter referred to as [1]) can be found in:

# Integer Programming and the Theory of Grouping
# Hrishikesh D. Vinod
# Journal of the American Statistical Association. Vol. 64, No. 326 (June 1969)
# pp. 506-519
# Stable URL: http://www.jstor.org/stable/2283635

def k_medoids(distances, number_clusters, timelimit=100, mipgap=0.0001):
    """
    Parameters
    ----------
    distances : 2d array
        Distances between each pair of node points. `distances` is a
        symmetrical matrix (dissimmilarity matrix).
    number_clusters : integer
        Given number of clusters.
    timelimit : integer
        Maximum time limit for the optimization.
    """

    # Distances is a symmetrical matrix, extract its length
    length = pyo.RangeSet(distances.shape[0])

    # Create model
    model = pyo.ConcreteModel("k-Medoids-Problem")
    model.cons = pyo.ConstraintList()

    # Create variables
    # x = {}  # Binary variables that are 1 if node i is assigned to cluster j
    # y = {}  # Binary variables that are 1 if node j is chosen as a cluster
    # for j in length:
    #     y[j] = model.Var(vtype="B", name="y_" + str(j))
    #
    #     for i in length:
    #         x[i, j] = model.Var(vtype="B",
    #                                name="x_" + str(i) + "_" + str(j))
    model.x = pyo.Var(length, length)
    model.y = pyo.Var(length)

    # Update to introduce the variables to the model
    # model.update()

    # Set objective - equation 2.1, page 509, [1]
    obj = pyo.quicksum(distances[i-1, j-1] * model.x[i, j] for i in length for j
                       in length)
    # pyo.quicksum(distances[i, j] * x[i, j] for i in range(length) for j
    #              in range(length), obj)
    model.obj = pyo.Objective(obj)

    # s.t.
    # Assign all nodes to clusters - equation 2.2, page 509, [1]
    # => x_i cannot be put in more than one group at the same time
    for i in range(length):
        model.cons.add(sum(x[i, j] for j in range(length)) == 1)

    # Maximum number of clusters - equation 2.3, page 509, [1]
    model.cons.add(sum(y[j] for j in range(length)) == number_clusters)

    # Prevent assigning without opening a cluster - equation 2.4, page 509, [1]
    for i in range(length):
        for j in range(length):
            model.cons.add(x[i, j] <= y[j])

    for j in range(length):
        model.cons.add(x[j, j] >= y[j])

    # Sum of main diagonal has to be equal to the number of clusters:
    model.cons.add(sum(x[j, j] for j in range(length)) == number_clusters)

    # Set solver parameters
    model.Params.TimeLimit = timelimit
    model.Params.MIPGap = mipgap
    model.Params.OutputFlag = False  # no console printing

    # Solve the model
    model.optimize()

    # Get results
    r_x = np.array([[x[i, j].X for j in range(length)]
                    for i in range(length)])

    r_y = np.array([y[j].X for j in range(length)])

    r_obj = model.ObjVal

    return r_y, r_x.T, r_obj


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
    (y, z, obj) = k_medoids(d, number_clusters, time_limit, mip_gap)

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


def cluster_2():
    pass


if __name__ == '__main__':
    pass
