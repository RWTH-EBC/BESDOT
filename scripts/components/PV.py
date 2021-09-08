from scripts.Component import Component
import pyomo.environ as pyo
import numpy as np
import pandas as pd
import warnings


class PV(Component):

    def __init__(self, comp_name, irr_profile, comp_type="PV", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['solar']
        self.outputs = ['elec']
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

    def _constraint_conser(self, model, flows, var_dict, T):
        """

        """
        output_powers = flows[self.output_energy][self.name][1]
        for t in T:
            model.cons.add(var_dict[('power', self.name)] * var_dict[(self.name, 'power_factors')][t]
                           == pyo.quicksum(var_dict[i][t] for i in output_powers))

    def _constraint_maxpower(self, model, flows, var_dict, T):
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

    # def add_variables(self, input_profiles, plant_parameters, var_dict, flows, model, T):
    #     """
    #     The PV generator should add solar irradiance and the pv generation
    #     additionally in the flow and var_dict.
    #     We calculate the pv generation p_output and set this as
    #     input of the pv generator while the efficiency of PV is
    #     1.
    #     """
    #     if self.name not in flows[self.input_energy].keys():
    #         flows[self.input_energy][self.name] = [[], []]
    #     input_flow = ('irr', self.name)  # Define input flow
    #     flows['solar'][self.name][0].append(input_flow)  # Add input flow to solar sector
    #     super().add_variables(input_profiles, plant_parameters, var_dict, flows, model, T)
    #     # power_pv = plant_parameters[(self.name, self.component_type)]['power']
    #
    #     g_t = np.array(input_profiles['irradiance'])
    #     # g_t = self.generate_g_t_series(np.array(input_parameters['bsrn_irradiance']), plant_parameters, T)
    #     # pv_output = self.calculate_pv_factors(input_profiles, g_t)*power_pv
    #     power_factors = self.calculate_pv_factors(input_profiles, g_t)
    #     power_factors[power_factors > 1] = 1  # make sure the power factors are in the correct range
    #     power_factors[power_factors < 0] = 0
    #     # self.pv_power_factors = self.calculate_pv_factors(input_profiles, g_t)
    #     # lb, ub = 0, power_pv
    #     # np.clip(pv_output, lb, ub, out=pv_output)
    #     # output_flow = (self.name, 'generation')
    #     var_dict[(self.name, 'power_factors')] = pd.Series(data=power_factors, index=T)
    #     # for t in T:
    #     #     model.add_component(self.name + '_' + 'power_factors' + '_%s' % t,
    #     #                         var_dict[(self.name, 'power_factors')][t])
