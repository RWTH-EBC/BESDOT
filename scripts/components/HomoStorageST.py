"""
Simplest model for hot water tank, in which the thermal storage is treated as a
homogeneous thermal capacity.
The unit of size of hot water storage is m³, could be liter, should pay
attention to the uniformity
"""

import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.HotWaterStorage import HotWaterStorage


class HomoStorageST(FluidComponent, HotWaterStorage):
    def __init__(self, comp_name, comp_type="HomoStorageST", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

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
        Compared with _constraint_conver, this function turn the pure power
        equation into an equation, which consider the temperature of output
        flows and input flows.
        Before using temperature in energy conservation equation,
        the temperature properties of storage should be defined in
        _read_temp_properties.
        Returns
        -------

        """
        water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
        water_density = 1000  # kg/m3
        unit_switch = 3600 * 1000  # J/kWh

        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        size = model.find_component('size_' + self.name)
        temp_var = model.find_component('temp_' + self.name)
        loss_var = model.find_component('loss_' + self.name)

        for t in range(len(model.time_step)-1):
            model.cons.add((temp_var[t+2] - temp_var[t+1]) * water_density *
                           size * water_heat_cap / unit_switch ==
                           input_energy[t+1] - output_energy[t+1] -
                           loss_var[t+1])

    def _constraint_loss(self, model, loss_type='off'):
        """
        According to loss_type choose the wanted constraint about energy loss
        of water tank.
        'off': no energy loss occurs
        """
        loss_var = model.find_component('loss_' + self.name)
        temp_var = model.find_component('temp_' + self.name)

        if loss_type == 'off':
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == 0)
        else:
            # FIXME (yni): The energy loss equation shouldn't be like the
            #  following format, which is only used for validation.
            # FiXME (yni): mindesten should be loss determined by the device
            #  size
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == 1.5 * ((temp_var[t + 1] -
                                                          20) / 1000))

    def _constraint_temp(self, model, init_temp=50, min_temp=30, max_temp=70):
        # Initial temperature for water in storage is define with a constant
        # value.
        temp_var = model.find_component('temp_' + self.name)
        model.cons.add(temp_var[1] == init_temp)
        for t in model.time_step:
            model.cons.add(temp_var[t] >= min_temp)
            model.cons.add(temp_var[t] <= max_temp)

        for heat_input in self.heat_flows_in:
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])

        for heat_output in self.heat_flows_out:
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])

    def _constraint_init_fluid_temp(self, model):
        """In a assumed state, the temperature of fluid flowing into storage at
        first time step should be set to an initial condition"""
        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            model.cons.add(t_in[1] == t_out[1])

        for heat_input in self.heat_flows_in:
            t_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            model.cons.add(t_in[1] == t_out[1])

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_loss(model, loss_type='off')
        self._constraint_temp(model)
        # self._constraint_init_fluid_temp(model)
        # todo (yni): the constraint about return temperature should be
        #  determined by consumer, fix this later
        # self._constraint_mass_flow(model)
        self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)

        # Method 1: Using the defined variable in building. heat_flows[(
        # input_comp, index)]['mass'] and heat_flows[(input_comp, index)][
        # 'temp'].
        # Method 2: Defining new variables and using new constraints to
        # connect the variable in component and building, just as energy flow.
        # first Method is chosen in 22.12.2021

        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        loss = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('loss_' + self.name, loss)
