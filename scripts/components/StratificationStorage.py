"""
Compared with HotWaterStorage, the storage tank is discretized vertically,
which is more realistic. The model is derived from the following paper.
Schütz, Thomas; Streblow, Rita; Müller, Dirk (2015): A comparison of thermal
energy storage models for building energy system optimization. In: Energy and
Buildings 93, S. 23–31. DOI: 10.1016/j.enbuild.2015.02.031.
"""
import warnings
import pyomo.environ as pyo
from scripts.components.HotWaterStorage import HotWaterStorage
import numpy as np


class StratificationStorage(HotWaterStorage):
    def __init__(self, comp_name, comp_type="StratificationStorage",
                 comp_model=None, min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size
                         )
        self.heat_flows_in = []  # The element in list should be dict,
        # which includes the tuples, in which shows  the relevant
        # heat flow variables.
        self.heat_flows_out = []

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

    def add_heat_flows(self, bld_heat_flows):
        # check the building heat flows and select the tuples related to this
        # device to add into list heat_flows.
        for element in bld_heat_flows:
            if self.name == element[0]:
                self.heat_flows_out.append(element)
            if self.name == element[1]:
                self.heat_flows_in.append(element)

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
        hot_water_mass = model.find_component('hot_water_mass_' + self.name)
        size = model.find_component('size_' + self.name)

        temp_var = model.find_component('temp_' + self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)
        loss_var = model.find_component('loss_' + self.name)
        # mass_flow_var = model.find_component('mass_flow_' + self.name)
        # analyze quantities of circulation for component.
        energy_flow = {}  # to storage all the energy flows in every circulation
        for heat_input in self.heat_flows_in:
            m_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'mass')
            t_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            energy_flow[heat_input] = model.find_component(heat_input[0] + '_' +
                                                           heat_input[1])
            for t in range(len(model.time_step)):
                model.cons.add(energy_flow[heat_input][t + 1] ==
                               (m_in[t + 1] * t_in[t + 1] - m_out[t + 1] *
                                t_out[t + 1]) * water_heat_cap / unit_switch)

        for heat_output in self.heat_flows_out:
            m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'mass')
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            energy_flow[heat_output] = model.find_component(heat_output[0] +
                                                            '_' +
                                                            heat_output[1])
            for t in range(len(model.time_step)):
                model.cons.add(energy_flow[heat_output][t + 1] ==
                               (m_out[t + 1] * t_out[t + 1] - m_in[t + 1] *
                                t_in[t + 1]) * water_heat_cap / unit_switch)

        # sum all energy flow for input energy and output energy
        for t in range(len(model.time_step)):
            model.cons.add(input_energy[t + 1] == sum(energy_flow[flow][t + 1]
                                                      for flow in
                                                      self.heat_flows_in))
            model.cons.add(output_energy[t + 1] == sum(energy_flow[flow][t + 1]
                                                       for flow in
                                                       self.heat_flows_out))

        for t in range(len(model.time_step)):
            # model.cons.add(output_energy[t+1] ==
            #               (temp_var[t+1] - return_temp_var[t+1]) *
            #               mass_flow_var[t+1] * water_heat_cap / unit_switch)
            model.cons.add(hot_water_mass[t+1] <= size*water_density*1000)

        for t in range(len(model.time_step) - 1):
            model.cons.add(water_heat_cap * (temp_var[t + 1] -
                                             return_temp_var[t + 1]) *
                           hot_water_mass[t + 2] == water_heat_cap * (
                           temp_var[t + 1] - return_temp_var[t + 1]) *
                           hot_water_mass[t + 1] -
                           m_in[t + 1] * water_heat_cap * (
                           temp_var[t + 1] - return_temp_var[t + 1])
                           + (input_energy[t + 1]-loss_var[t+1]) * unit_switch)

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
            # The energy loss equation shouldn't be like the following
            # format, which is only used for validation.
            # FiXME (yni): mindesten should be loss determined by the device
            #  size, need a proved model from simulation or experiment
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == 1.5 * ((temp_var[t + 1] -
                                                          20) / 1000))

    def _constraint_temp(self, model, init_temp=60):
        # Initial temperature for water in storage is define with a constant
        # value.
        temp_var = model.find_component('temp_' + self.name)
        for t in model.time_step:
            model.cons.add(temp_var[t] == init_temp)
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

    def _constraint_return_temp(self, model, init_temp=20):
        # The first constraint for return temperature. Assuming a constant
        # temperature difference between flow temperature and return
        # temperature.
        return_temp_var = model.find_component('return_temp_' + self.name)
        for t in model.time_step:
            model.cons.add(return_temp_var[t] == init_temp)
        for heat_input in self.heat_flows_in:
            t_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(return_temp_var[t + 1] == t_in[t + 1])

        for heat_output in self.heat_flows_out:
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(return_temp_var[t + 1] == t_in[t + 1])

    def _constraint_mass_flow(self, model):
        # The mass flow set to be constant as circulation pumps
        # mass flow unit kg/h

        for heat_input in self.heat_flows_in:
            m_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'mass')
            for t in range(len(model.time_step)):
                model.cons.add(m_in[t + 1] == m_out[t + 1])
                # todo (yni): default value is used for mass flow

        for heat_output in self.heat_flows_out:
            m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'mass')
            for t in range(len(model.time_step)):
                model.cons.add(m_in[t + 1] == m_out[t + 1])

    def _constraint_hot_water_mass(self, model, init_mass=0.5):
        hot_water_mass = model.find_component('hot_water_mass_' + self.name)
        size = model.find_component('size_' + self.name)
        model.cons.add(hot_water_mass[1] == init_mass*size*1000)
        # todo (yca): add commit for density and even use formate in line 65,
        #  make sure that the size unit is same for all constrains

    def _constraint_input_permit(self, model, min_mass=0.2,
                                 max_mass=0.8,
                                 init_status='off'):
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
        input_energy = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        size = model.find_component('size_' + self.name)
        hot_water_mass = model.find_component('hot_water_mass_' + self.name)

        # Initial status should be determined by us.
        if init_status == 'on':
            model.cons.add(status_var[1] == 1)
        elif init_status == 'off':
            model.cons.add(status_var[1] == 0)

        for t in range(len(model.time_step)-1):
            # Need a better tutorial for introducing the logical condition
            model.cons.add(status_var[t + 2] >= small_num *
                           (small_num + (max_mass*size*1000 -
                                         min_mass*size*1000 - small_num) *
                            status_var[t+1] + min_mass*size*1000 -
                            hot_water_mass[
                                t+1]))
            model.cons.add(status_var[t + 2] <= 1 + small_num *
                           (small_num + (max_mass*size*1000 -
                                         min_mass*size*1000 - 2 *
                                         small_num) *
                            status_var[t + 1] + min_mass*size*1000 -
                            hot_water_mass[t + 1]))
            model.cons.add(input_energy[t + 1] == input_energy[t + 1] *
                           status_var[t + 1])
        model.cons.add(input_energy[len(model.time_step)] ==
                       input_energy[len(model.time_step)] *
                       status_var[len(model.time_step)])

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_loss(model, loss_type='off')
        self._constraint_temp(model)
        self._constraint_return_temp(model)
        self._constraint_mass_flow(model)
        self._constraint_hot_water_mass(model)
        self._constraint_vdi2067(model)
        self._constraint_input_permit(model)

    def add_vars(self, model):
        super().add_vars(model)

        # fixme (yca): temp and return_temp are constant, so it is not
        #  necessary to define pyo.Var for them
        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        return_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('return_temp_' + self.name, return_temp)

        # mass_flow = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('mass_flow_' + self.name, mass_flow)

        loss = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('loss_' + self.name, loss)

        hot_water_mass = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('hot_water_mass_' + self.name,
                            hot_water_mass)

    
