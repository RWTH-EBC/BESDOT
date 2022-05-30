"""
Simplest model for hot water tank, in which the thermal storage is treated as a
homogeneous thermal capacity.
The unit of size of hot water storage is m³, could be liter, should pay
attention to the uniformity
"""

import warnings
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.FluidComponent import FluidComponent
from scripts.components.HotWaterStorage import HotWaterStorage

small_num = 0.0001


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
            self.max_temp = 95

        if 'min temperature' in properties.columns:
            self.min_temp = float(properties['min temperature'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for min temperature.")
            self.min_temp = 30

        if 'init temperature' in properties.columns:
            self.init_temp = float(properties['init temperature'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for min temperature.")
            self.init_temp = 60

        if 'loss type' in properties.columns:
            self.loss_type = float(properties['loss type'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for loss type.")
            self.loss_type = 'off'

        if 'init status' in properties.columns:
            self.min_temp = float(properties['init status'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for init status.")
            self.init_status = 'on'

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

    def _constraint_loss(self, model):
        """
        According to loss_type choose the wanted constraint about energy loss
        of water tank.
        'off': no energy loss occurs
        """
        loss_var = model.find_component('loss_' + self.name)
        temp_var = model.find_component('temp_' + self.name)
        size = model.find_component('size_' + self.name)

        if self.loss_type == 'off':
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == 0)
        else:
            # FIXME (yni): The energy loss equation supposed to be unchanged,
            #  but the hard coding values are not be validated. It should be
            #  got from a plausible resource
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == 0.6 * ((temp_var[t + 1] -
                                                          20) / 1000 * size))

    def _constraint_temp(self, model):
        # Initial temperature for water in storage is define with a constant
        # value.
        temp_var = model.find_component('temp_' + self.name)
        model.cons.add(temp_var[1] == self.init_temp)
        for t in model.time_step:
            model.cons.add(self.max_temp >= temp_var[t])
            model.cons.add(self.min_temp <= temp_var[t])

        for heat_input in self.heat_flows_in:
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            for t in range(len(model.time_step)):
                model.cons.add(temp_var[t + 1] == t_out[t + 1])
        for heat_output in self.heat_flows_out:
            t_out = model.find_component(
                heat_output[0] + '_' + heat_output[1] + '_' + 'temp')
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

    def _constraint_input_permit(self, model):
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
        if self.init_status == 'on':
            model.cons.add(status_var[1] == 1)
        elif self.init_status == 'off':
            model.cons.add(status_var[1] == 0)

        for t in range(len(model.time_step)-1):
            # Need a better tutorial for introducing the logical condition
            model.cons.add(status_var[t + 2] >= small_num *
                           (small_num + (self.max_temp - self.min_temp -
                                         small_num) * status_var[t+1] +
                            self.min_temp - temp_var[t+2]))
            model.cons.add(status_var[t + 2] <= 1 + small_num *
                           (small_num + (self.max_temp - self.min_temp - 2 *
                                         small_num) * status_var[t + 1] +
                            self.min_temp - temp_var[t + 2]))
            # fixme (yni): the following equation is wrong!!!, that could be
            #  problematic.
            model.cons.add(input_energy[t + 1] == input_energy[t + 1] *
                           status_var[t + 1])
            # Additional constraint for allowed temperature in storage
            #model.cons.add(temp_var[t + 2] >= min_temp)
            #model.cons.add(temp_var[t + 2] <= max_temp)
        model.cons.add(input_energy[len(model.time_step)] ==
                       input_energy[len(model.time_step)] *
                       status_var[len(model.time_step)])

    def _constraint_input_permit_gdp(self, model):
        """
        This function use the pyomo GDP model to replace the original constraint
        for input permit. It would be easier to generate the control model.
        Args:
            model: pyomo model for the project
            min_temp: the set minimal temperature
            max_temp: the set maximal temperature
            init_status: determine the initial status of energy supplier.
        Returns:
            None
        """
        temp_var = model.find_component('temp_' + self.name)
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        model.init = pyo.BooleanVar()

        if self.init_status == 'on':
            model.init_log = pyo.LogicalConstraint(
                expr=model.init.equivalent_to(True))
        elif self.init_status == 'off':
            model.init_log = pyo.LogicalConstraint(
                expr=model.init.equivalent_to(False))

        for t in model.time_step:
            a = Disjunct()
            c_1 = pyo.Constraint(expr=temp_var[t] >= self.max_temp)
            c_2 = pyo.Constraint(expr=input_energy[t] == 0)
            model.add_component('a_dis_' + str(t), a)
            a.add_component('a_1_' + str(t), c_1)
            a.add_component('a_2_' + str(t), c_2)

            b = Disjunct()
            c_7 = pyo.Constraint(expr=temp_var[t] <= self.max_temp - small_num)
            model.add_component('b_dis_' + str(t), b)
            b.add_component('b_1_' + str(t), c_7)

            c = Disjunct()
            c_3 = pyo.Constraint(expr=temp_var[t] <= self.min_temp)
            model.add_component('c_dis_' + str(t), c)
            c.add_component('c_' + str(t), c_3)

            d = Disjunct()
            c_4 = pyo.Constraint(expr=input_energy[t] == 0)
            c_6 = pyo.Constraint(expr=temp_var[t] >= self.min_temp + small_num)
            model.add_component('d_dis_' + str(t), d)
            d.add_component('d_' + str(t), c_4)
            d.add_component('d_2_' + str(t), c_6)

            dj = Disjunction(expr=[a, b, c, d])
            model.add_component('dj_dis_' + str(t), dj)

            if t == 1:
                p_4 = pyo.LogicalConstraint(
                    expr=model.init.equivalent_to(
                        pyo.lor(a.indicator_var, b.indicator_var)))
                p_5 = pyo.LogicalConstraint(
                    expr=~model.init.equivalent_to(
                        pyo.lor(c.indicator_var, d.indicator_var)))
            else:
                last_status = model.find_component('b_dis_' + str(t - 1))
                p_4 = pyo.LogicalConstraint(
                    expr=pyo.lor(a.indicator_var,
                                 b.indicator_var).equivalent_to(
                        last_status.indicator_var))
                p_5 = pyo.LogicalConstraint(
                    expr=~last_status.indicator_var.equivalent_to(
                        pyo.lor(c.indicator_var, d.indicator_var)))
            model.add_component('p_4_' + str(t), p_4)
            model.add_component('p_5_' + str(t), p_5)

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_loss(model, loss_type='on')
        self._constraint_temp(model)
        # self._constraint_init_fluid_temp(model)
        # todo (yni): the constraint about return temperature should be
        #  determined by consumer, fix this later
        # self._constraint_mass_flow(model)
        #todo: unterschiedliche Wärmekapazität
        #self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        # self._constraint_input_permit(model, min_temp=30, init_status='on')
        self._constraint_vdi2067(model)

        if self.cluster is not None:
            self._constraint_conserve(model)
        else:
            self._constriant_unchange(model)

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
