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


class HomoStorage(FluidComponent, HotWaterStorage):
    def __init__(self, comp_name, comp_type="HomoStorage", comp_model=None,
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

    def _constraint_temp(self, model, init_temp=58):
        # Initial temperature for water in storage is define with a constant
        # value.
        temp_var = model.find_component('temp_' + self.name)
        model.cons.add(temp_var[1] == init_temp)

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

    # def _constraint_return_temp(self, model):
    #     # The first constraint for return temperature. Assuming a constant
    #     # temperature difference between flow temperature and return
    #     # temperature.
    #     delta_temp = 20  # unit K
    #     min_delta_temp = 0
    #     temp_var = model.find_component('temp_' + self.name)
    #     return_temp_var = model.find_component('return_temp_' + self.name)
    #
    #     for t in model.time_step:
    #         model.cons.add(temp_var[t] - return_temp_var[t] <= delta_temp)
    #         model.cons.add(temp_var[t] - return_temp_var[t] >= min_delta_temp)

    def _constraint_input_permit(self, model, min_temp=40, max_temp=90,
                                 init_status='on'):
        """
        The input to water tank is controlled by tank temperature, which is
        close to reality. When the temperature of water tank reaches the
        minimal allowed temperature, the input to tank is on. If the
        temperature of water tank reaches maximal allowed temperature,
        the input should be off.
        The minimal and maximal temperature could be given from the tank
        manufacturer or by the system designer.
        This constraint uses binary variable to judge whether it meets the
        conditions. So the calculation cost rise huge.
        """
        # Define the status variable to determine, if input is permitted.
        # The variable won't be used, if this constraint is not added to
        # model, so prefer to define them under this method.
        status_var = pyo.Var(model.time_step, domain=pyo.Binary)
        model.add_component('status_' + self.name, status_var)
        # Small number, which used to turn logical conditions to mathematical
        # condition. Attention! The built condition modell could be problematic!
        # Decrease the small number value could solve the problem
        small_num = 0.00001

        temp_var = model.find_component('temp_' + self.name)
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)

        # Initial status should be determined by us.
        if init_status == 'on':
            model.cons.add(status_var[1] == 1)
        elif init_status == 'off':
            model.cons.add(status_var[1] == 0)

        for t in range(len(model.time_step)-1):
            # Need a better tutorial for introducing the logical condition
            model.cons.add(status_var[t + 2] >= small_num *
                           (small_num + (max_temp - min_temp - small_num) *
                            status_var[t+1] + min_temp - temp_var[t+1]))
            model.cons.add(status_var[t + 2] <= 1 + small_num *
                           (small_num + (max_temp - min_temp - 2 * small_num) *
                            status_var[t + 1] + min_temp - temp_var[t + 1]))
            # fixme (yni): the following equation is wrong!!!, that could be
            #  problematic.
            model.cons.add(input_energy[t + 1] == input_energy[t + 1] *
                           status_var[t + 1])
        model.cons.add(input_energy[len(model.time_step)] ==
                       input_energy[len(model.time_step)] *
                       status_var[len(model.time_step)])

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_loss(model, loss_type='off')
        self._constraint_temp(model)
        # todo (yni): the constraint about return temperature should be
        #  determined by consumer, fix this later
        # self._constraint_return_temp(model)
        self._constraint_mass_flow(model, mass_flow=100)
        self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        self._constraint_input_permit(model, min_temp=55, init_status='on')
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
