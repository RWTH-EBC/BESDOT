"""
Compared with HotWaterStorage, the storage tank is discretized vertically,
which is more realistic. The model is derived from the following paper.
Schütz, Thomas; Streblow, Rita; Müller, Dirk (2015): A comparison of thermal
energy storage models for building energy system optimization. In: Energy and
Buildings 93, S. 23–31. DOI: 10.1016/j.enbuild.2015.02.031.
"""
import warnings
import pyomo.environ as pyo
from scripts.components.Storage import Storage
import numpy as np


class StratificationStorage(Storage):
    def __init__(self, comp_name, comp_type="StratificationStorage",
                 comp_layer=2, comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
    model.layer = pyo.RangeSet(1, comp_layer+1)

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if 'max temperature' in properties.columns:

            self.max_temp = float(properties['max temperature'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for max temperature.")
        if 'min temperature' in properties.columns:
            self.min_temp = float(properties['min temperature'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for min temperature.")

    def _constraint_conver(self, model):
        """
        Compared with _constraint_conser, this function turn the pure power
        equation into an equation, which consider the temperature of output
        flows and input flows.
        Before using temperature in energy conservation equation,
        the temperature properties of storage should be defined in
        _read_temp_properties.
        Returns
        -------

        """
        water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
        water_density = 1  # kg/l
        unit_switch = 3600 * 1000  # J/kWh

        input_energy = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        heat_water_percent = model.find_component('heat_water_percent_' +
                                                  self.name, heat_water_percent)
        size = model.find_component('size_' + self.name)

        temp_var = model.find_component('temp_' + self.name)
        loss_var = model.find_component('loss_' + self.name)
        mass_flow_var = model.find_component('mass_flow_' + self.name)
        
        # Backup: nom_capacity should be a variable, not a constraint.
        #  right?

        for t in range(len(model.time_step)-1):
            # todo (yca): think about the meaning of the constraint. This one
            #  is used for HomoStorage, should be changed for StratStorage
            #  with the variable heat_water_percent.
            model.cons.add(sum((temp_var[l, t + 2] - temp_var[l, t + 1]) *
                           water_density *
                           size * heat_water_percent[l, t + 1]) *
                           water_heat_cap /
                           unit_switch ==
                           input_energy[t + 1] - output_energy[t + 1] -
                           loss_var[t + 1] for l in model.layer)
        model.cons.add(sum((temp_var[l, 1] - temp_var[l,
                                                      len(model.time_step)]) *
                       water_density * size * heat_water_percent[l, t + 1]) *
                       water_heat_cap / unit_switch ==
                       input_energy[len(model.time_step)] -
                       output_energy[len(model.time_step)] -
                       loss_var[len(model.time_step)] for l in model.layer)

        for t in range(len(model.time_step)):
            model.cons.add(output_energy[t + 1] ==
                           (temp_var[1, t + 1] - temp_var[len(model.layer), t +
                                                              1]) *
                           mass_flow_var[t + 1] * water_heat_cap / unit_switch)
            # FIXME (yni): The energy loss equation shouldn't be like the
            #  following format, which is only used for validation.
            model.cons.add(loss_var[t+1] == 1.5 * ((temp_var[1, t+1] - 20) /
                                                   1000))

    def _constraint_temp(self, model):
        # Initial temperature for water in storage is define with a constant
        # value, maybe later could change to others, like air temperature at
        # time step 0.
        temp_var = model.find_component('temp_' + self.name)
        #return_temp_var = model.find_component('return_temp_' + self.name)
        loss_var = model.find_component('loss_' + self.name)
        mass_flow_var = model.find_component('mass_flow_' + self.name)

        # tank的初始温度
        model.cons.add(temp_var[1, 1] == 60)
        # tank的回水温度
        model.cons.add(temp_var[len(model.layer), 1] == 20)
        model.cons.add(mass_flow_var[1]== 0)
        # 质量的初始流量

        for t in model.time_step:
            model.cons.add(temp_var[1, t] <= self.max_temp)
            # model.cons.add(temp_var[t] >= self.min_temp)
            model.cons.add(temp_var[len(model.layer), t] <= self.max_temp)
            # model.cons.add(return_temp_var[t] >= self.min_temp)
            # 出水温度等于上层温度

    def _constraint_return_temp(self, model):
        # The first constraint for return temperature. Assuming a constant
        # temperature difference between flow temperature and return
        # temperature.
        delta_temp = 20  # unit K
        min_delta_temp = 0
        temp_var = model.find_component('temp_' + self.name)
        # 回水温度出水温度温差小于最大温差
        for t in model.time_step:
            model.cons.add(temp_var[1, t] - temp_var[
                len(model.layer), t] <= delta_temp)
            model.cons.add(temp_var[1, t] - temp_var[
                len(model.time_step), t] >= min_delta_temp)

    def _constraint_heat_water_percent(self, model):
        heat_water_percent = model.find_component('heat_water_percent_' +
                                                  self.name)
        # 上下层热水百分比相加等于1
        for t in model.time_step:
            model.cons.add(sum(heat_water_percent[l, t] for l in model.layer)
                           == 1)

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_temp(model)
        self._constraint_return_temp(model)
        self._constraint_vdi2067(model)
        self._constraint_heat_water_percent(model)

    def add_vars(self, model):
        super().add_vars(model)
        #layer = np.arange(pyo.lay_num)
        # Fixme (yca): RangeSet is not defined with pyomo Interger, should be
        #  python int value

        temp = pyo.Var(model.layer, model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        mass_flow = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('mass_flow_' + self.name, mass_flow)

        loss = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('loss_' + self.name, loss)

        heat_water_percent = pyo.Var(model.layer, model.time_step, bounds=(0, 
                                                                          1))
        model.add_component('heat_water_percent_' + self.name,
                            heat_water_percent)

       


    
