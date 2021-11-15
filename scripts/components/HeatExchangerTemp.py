from scripts.Component import Component
import pyomo.environ as pyo


class HeatExchangerTemp(Component):
    """
    HeatExchangerTemp is also a class for heat exchanger. Compared to
    HeatExchanger, this model considers the temperature variable and mass
    flow at the both side.
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
        water_density = 1000  # kg/m3
        unit_switch = 3600 * 1000  # J/kWh

        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)

        temp_var = model.find_component('temp_' + self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)
        loss_var = model.find_component('loss_' + self.name)
        mass_flow_var = model.find_component('mass_flow_' + self.name)

        for t in range(len(model.time_step)-1):
            model.cons.add(input_energy[t+1] * (1 - loss_var[t+1]) ==
                           output_energy[t+1])

        for t in range(len(model.time_step)):
            model.cons.add(output_energy[t+1] ==
                           (temp_var[t+1] - return_temp_var[t+1]) *
                           mass_flow_var[t+1] * water_heat_cap / unit_switch)

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

    def _constraint_heat_transfer(self, model):
        """
        The simulation of heat transfer according to heat exchanger working
        principle for counter flow. Attention this is only possible with 4
        temperature variables (primary inflow and return flow, secondary
        inflow and return flow).
        """
        pass

    def add_vars(self, model):
        super().add_vars(model)

        # These temperature variables and mass flow variables represent the
        # variable of building side.
        bld_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('bld_temp_' + self.name, bld_temp)

        bld_return_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('bld_return_temp_' + self.name, bld_return_temp)

        bld_mass_flow = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('bld_mass_flow_' + self.name, bld_mass_flow)

        # These temperature variables and mass flow variables represent the
        # variable of network side.
        net_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('net_temp_' + self.name, net_temp)

        net_return_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('net_return_temp_' + self.name, net_return_temp)

        net_mass_flow = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('net_mass_flow_' + self.name, net_mass_flow)

        # The energy loss is considered, because of the heat transfer to the
        # environment.
        loss = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('loss_' + self.name, loss)
