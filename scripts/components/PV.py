from scripts.Component import Component
import pyomo.environ as pyo
import numpy as np
import pandas as pd
import warnings


class PV(Component):

    def __init__(self, comp_name, irr_profile, comp_type="PV", comp_model=None):
        self.inputs = ['solar']
        self.outputs = ['elec']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)

        self.irr_profile = irr_profile

    def _read_properties(self, properties):
        """
        The PV model utilizes additionally temperature coefficient and NOCT
        (Nominal Operating Cell Temperature) to calculate the pv factor,
        besides all universal properties
        """
        super()._read_properties(properties)
        if 'temp coefficient' in properties.columns:
            self.temp_coefficient = float(properties['temp coefficient'])
        elif 'temp_coefficient' in properties.columns:
            self.temp_coefficient = float(properties['temp_coefficient'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for temp coefficient")
        if 'NOCT' in properties.columns:
            self.noct = float(properties['NOCT'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for NOCT")

    def _constraint_maxpower(self, model):
        """
        The max. power check of PV is not necessary if the power factors are in the range from
        0 to 1
        """
        pass

    def calculate_pv_factors(self, input_parameters, g_t):
        air_temp = np.array(input_parameters['air_temperature'])
        cell_temp = air_temp + np.multiply((g_t/800), (self.noct-20))
        pv_factors = np.multiply((g_t/1000), (1-np.multiply(self.temp_coefficient, (cell_temp-25))))
        return pv_factors


if __name__ == '__main__':
    pv = PV(comp_name='test_pv', irr_profile=[100, 200, 300], comp_type="PV",
            comp_model='PV1')
