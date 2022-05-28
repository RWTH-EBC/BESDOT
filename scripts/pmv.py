"""
Simplified Modell for internal use.
"""

import os
from warnings import warn
import pyomo.environ as pyo
import pandas as pd
import numpy as np
import tsam.timeseriesaggregation as tsam
from tools.k_medoids import cluster

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_path = os.path.join(base_path, "data", "weather_data",
                           "Dusseldorf", "pmv_coeff.csv")
data = pd.read_csv(output_path)
pmv = data.loc[:, 'coeff']
b = pmv.values.tolist()

class PMV(object):
    def __init__(self, name, typ):
        self.name = name
        self.typ = typ



    def _constraint_pmv(self, model):
        """
        Calculate the COP value in each time step, with default set
        temperature of 60 degree and machine efficiency of 40%.
        """
        pa = model.find_component('pa')
        pmv = model.find_component('pmv')
        temp_zoom = model.find_component('temp_zoom')
        for t in model.time_step:
            coeff = eval(b[t])
            model.cons.add(pa[t] == (85.165 * temp_zoom[t] - 539.063))
            model.cons.add(pmv[t] == (coeff[0] * temp_zoom[t] +
                                      coeff[1] * pa[t] - coeff[2]))

    def add_cons(self, model):
        self. _constraint_pmv(model)

    def add_vars(self, model):
        super().add_vars(model)

        temp_zoom = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_zoom', temp_zoom)

        pa = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('pa', pa)

