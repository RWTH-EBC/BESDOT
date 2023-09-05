"""
vdi2067 provide a detailed process to calculate annuity for investigation and
operation cost. This tool helps to calculate the annuity from the total
investigation.
"""
# from datetime import timedelta
# import pandas as pd
import numpy as np


def annuity_factor(t, q=1.007):
    # q: interest factor (taken from Bundesministerium der Finanzen)
    if q == 1.0:
        annuity = 1 / t
    else:
        try:
            annuity = (q - 1) / (1 - pow(q, -t))
        except ZeroDivisionError:
            raise ValueError('Cannot calculate annuity')
    return annuity


def dynamic_cash_value(t, q=1.007, r=1.03):
    # q: interest factor (taken from Bundesministerium der Finanzen)
    if r == q:
        b = t / q
    else:
        b = (1 - pow(r / q, t)) / (q - r)
    return b


def calc_capital_cost(t, t_n, q, ann, a_0):
    """
    value for r taken from Statistisches Bundesamt:
    median of yearly price index change for central heating devices (GP 25 21)

    t: observation period, in year
    t_n: service life of the equipment, in year
    q: interest factor
    ann: annuity factor
    a_0: investment amount in first year

    n: number of replacements
    r_w: residual value
    r: price change factor, may vary according to different equipment
    """
    r = 1.02
    n = np.ceil(t / t_n) - 1
    r_w = a_0 * pow(r, n * t_n) * ((n + 1) * t_n - t) / t_n * 1 / pow(q, t)

    # np.ceil gives a float64 -> do int(n) for range
    a_inv = []
    for i in range(int(n) + 1):
        a_i = a_0 * ((pow(r, i * t_n)) / (pow(q, i * t_n)))
        a_inv.append(a_i)

    a_n_k = (sum(a_inv) - r_w) * ann
    return a_n_k


def calc_operation_cost(t, q, ann, a_0, f_inst, f_w, f_op):
    """
    t: observation period, in year
    q: interest factor
    ann: annuity factor
    a_0: investment amount in first year
    f_inst: float, factor for repair effort (from VDI2067)
    f_w: float, factor for servicing and inspection effort (from VDI2067)
    f_op: int, effort for operation in h/a (from VDI2067)

    values for r and price_op taken from Statistisches Bundesamt
    r_b: price change factor for actual operation, for labour cost (vdi 2067)
    r_in: price change factor for maintenance (vdi 2067)
    b_b: cash value factor for actual operation
    b_in: cash value factor for maintenance
    price_op: labour costs per hour worked (2019)
    """
    r_b = 1.02
    r_in = 1.03
    b_b = dynamic_cash_value(t, q, r_b)
    b_in = dynamic_cash_value(t, q, r_in)

    # disable a_b1 first for this cost doesn't exist when cap is 0!
    # The value of this is little for large system and too much for small system!
    # a_b1 = f_op * price_op
    a_b1 = 0
    a_in = a_0 * (f_inst + f_w)

    a_n_b = a_b1 * ann * b_b + a_in * ann * b_in
    return a_n_b


def calc_annuity(t_n, invest_neu, f_inst, f_w, f_op):
    """
    This function calculates the annuity of technical building installations
    according to VDI 2067.

    params:
    T: time series, indicates the observation period
    t_n: service life of the equipment, in year
    invest (c in BaseBoiler): float or pyomo variable, investment cost in [
    EUR/kW] or [EUR/kWh], fixed value for each component or calculated variable
    cap: power or capacity of the component in [kW] or [kWh]
    f_inst: float, factor for repair effort (from VDI2067)
    f_w: float, factor for servicing and inspection effort (from VDI2067)
    f_op: int, effort for operation in h/a (from VDI2067)

    t: observation period, in year: calculated from time series
    q: interest factor (taken from Bundesministerium der Finanzen)
    a_0: initial investment amount

    a_n_e: annuity of revenue, like feed in electricity
    a_n_v: annuity of demand related cost, like purchased gas or electricity
    a_n_s: annuity of other cost

    returns:
    a_n: annuity (one year) for the technical building installation
    """
    t = 20  # year
    # todo: the observation year should be considered in the environment
    #  object, which is usually 20 years. But this doesn't matter much. so
    #  just leave it.

    q = 1.07

    ann = annuity_factor(t, q)
    a_0 = invest_neu

    # The revenue and demand related cost are set in the energy management
    # system class. Because the cost are related to the model variables.
    # WARN: in the energy management system class the cash value factor is
    # not considered, because the observation is only 1 year. If the
    # observation period longer than 1 year, should use the cash value factor
    # for demand related cost and revenue as well
    a_n_e = 0
    a_n_v = 0
    a_n_s = 0

    a_n = (calc_capital_cost(t, t_n, q, ann, a_0) + a_n_v
           + calc_operation_cost(t, q, ann, a_0, f_inst, f_w, f_op) +
           a_n_s) - a_n_e

    return a_n


"""
if __name__ == "__main__":
    # validation for optimisation results

    time_steps = pd.date_range(start="1/1/2019", end="31/12/2019")
    t_n = 20
    invest = 200
    cap = 1.17
    f_inst = 0.01
    f_w = 0.015
    f_op = 20
    a_n = run(time_steps, t_n, invest, cap, f_inst, f_w, f_op)
    print(a_n)
"""

"""
invest = 3600
subsidy = 2160
t_n = 20
f_inst = 0.01
f_w = 0.015
f_op = 20

annuity = calc_annuity(t_n, invest - subsidy, f_inst, f_w, f_op)
print("Annuity for the PV component: {:.8f} EUR/year".format(annuity))
"""
