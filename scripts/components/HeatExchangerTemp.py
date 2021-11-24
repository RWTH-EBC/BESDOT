from scripts.Component import Component
import pyomo.environ as pyo


class HeatExchangerTemp(Component):
    """
    HeatExchangerTemp is also a class for heat exchanger. Compared to
    HeatExchanger, this model considers the temperature variable and mass
    flow at the both side.
    The high-temperature side is indicated by indices 'h' and the
    low-temperature side by indices 'c'
    """

    def __init__(self, comp_name, comp_type="HeatExchangerTemp",
                 comp_model=None, min_size=0, max_size=1000, current_size=0):
        self.inputs = ['heat']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_conver(self, model):
        """
        Using Temperature and mass flow to calculate the input energy and
        output energy.
        Attention: The heat exchanger, which is used in haus station for heat
        network, runs usually in counter flow.
        """
        water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
        unit_switch = 3600 * 1000  # J/kWh

        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)

        temp_h = model.find_component('temp_h_' + self.name)
        return_temp_h = model.find_component('return_temp_h_' + self.name)
        mass_flow_h = model.find_component('mass_flow_h_' + self.name)
        temp_c = model.find_component('temp_c_' + self.name)
        return_temp_c = model.find_component('return_temp_c_' + self.name)
        mass_flow_c = model.find_component('mass_flow_c_' + self.name)
        loss_var = model.find_component('loss_' + self.name)

        for t in range(len(model.time_step)):
            model.cons.add(input_energy[t+1] * (1 - loss_var[t+1]) ==
                           output_energy[t+1])
            model.cons.add(output_energy[t+1] == (temp_c[t+1] -
                                                  return_temp_c[t+1]) *
                           mass_flow_c[t+1] * water_heat_cap / unit_switch)
            model.cons.add(input_energy[t+1] == (temp_h[t+1] -
                                                 return_temp_h[t+1]) *
                           mass_flow_h[t+1] * water_heat_cap / unit_switch)

    def _constraint_loss(self, model, loss_type='off'):
        """
        According to loss_type choose the wanted constraint about energy loss
        of water tank.
        'off': no energy loss occurs
        'foam': efficient insulation according to the product introauction.
        https://www.pewo.com/technologien/warmedammung-und-kalteisolierung/
        todo: calculate a default value with given thermal conductivity
        Attention: The temperature difference for loss calculation is the
        difference between fluid and air temperature in the equipment room,
        which is usually warmer than outdoor air temperature.
        """
        loss_var = model.find_component('loss_' + self.name)
        temp_var = model.find_component('temp_' + self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)

        if loss_type == 'off':
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == 0)
        elif loss_type == 'foam':
            # with the assumption of an product and air temperature in
            # equipment room to calculate an default value.
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == (temp_var[t+1] +
                                                   return_temp_var[t+1] - 50)
                               / 1000 * input_energy[t+1])
        else:
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == 1.5 * ((temp_var[t + 1] -
                                                          20) / 1000))

    def _constraint_delta_temp(self, model):
        """
        Calculation the heat flow with temperature difference between hot
        medium and cool medium.
        Q = k * A * delta_T
        delta_T could be calculated with arithmetic mean value or logarithmic
        mean value. Taking into account the complexity of model, the arithmetic
        mean value is used. If necessary could change to logarithmic mean value.
        """
        temp_h = model.find_component('temp_h_' + self.name)
        return_temp_h = model.find_component('return_temp_h_' + self.name)
        temp_c = model.find_component('temp_c_' + self.name)
        return_temp_c = model.find_component('return_temp_c_' + self.name)
        delta_temp = model.find_component('delta_temp_' + self.name)

        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)

        for t in range(len(model.time_step)):
            model.cons.add(delta_temp == (temp_h + return_temp_h - temp_c -
                                          return_temp_c) / 2)
            model.cons.add(input_energy[t+1] == (temp_h[t + 1] -
                                                   return_temp_h[t + 1]) *
                           mass_flow_h[t + 1] * water_heat_cap / unit_switch)

    def add_vars(self, model):
        super().add_vars(model)

        # These temperature variables and mass flow variables represent the
        # variable of high temperature side. In haus station is the network
        # side.
        temp_h = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_h_' + self.name, temp_h)

        return_temp_h = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('return_temp_h_' + self.name, return_temp_h)

        mass_flow_h = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('mass_flow_h_' + self.name, mass_flow_h)

        # These temperature variables and mass flow variables represent the
        # variable of low temperature side. which represent haus side in haus
        # station.
        temp_c = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_c_' + self.name, temp_c)

        return_temp_c = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('return_temp_c_' + self.name, return_temp_c)

        mass_flow_c = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('mass_flow_c_' + self.name, mass_flow_c)

        # Temperature difference value
        delta_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('delta_temp_' + self.name, delta_temp)

        # The energy loss is considered, because of the heat transfer to the
        # environment.
        loss = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('loss_' + self.name, loss)
