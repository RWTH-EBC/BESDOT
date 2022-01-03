import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.HeatExchanger import HeatExchanger


class HeatExchangerFluid(FluidComponent, HeatExchanger):
    """
    HeatExchangerFluid is also a class for heat exchanger. Compared to
    HeatExchanger, this model considers the temperature variable and mass
    flow at the both side.
    The high-temperature side is indicated by indices 'h' and the
    low-temperature side by indices 'c'. Attention, the heat exchanger is
    designed for heat supply. So the energy input means the fluid with high
    temperature.
    The variable 'size' is set the exchanger area with unit of m2.
    """

    def __init__(self, comp_name, comp_type="HeatExchangerFluid",
                 comp_model=None, min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        if len(self.heat_flows_in) > 1:
            warnings.warn('more than one energy flow input is given for the '
                          'heat exchanger')
        if len(self.heat_flows_out) > 1:
            warnings.warn('more than one energy flow output is given for the '
                          'heat exchanger')

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if 'k' in properties.columns:
            self.k = float(properties['k'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for k.")

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
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        # Under the assumption, that the energy loss depends on the fluid
        # temperature of energy output side, namely the lower temperature side.
        # That could be change to input side or even the mean value of these
        # four temperature.
        heat_output = self.heat_flows_out[0]
        t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                    '_' + 'temp')
        t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                     '_' + 'temp')

        if loss_type == 'off':
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == 0)
        elif loss_type == 'foam':
            # with the assumption of an product and air temperature in
            # equipment room to calculate an default value.
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == (t_in[t+1] + t_out[t+1] - 50)
                               / 1000 * input_energy[t+1])
        else:
            for t in range(len(model.time_step)):
                model.cons.add(loss_var[t + 1] == 1.5 * ((t_in[t + 1] -
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
        heat_input = self.heat_flows_in[0]
        temp_h = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                      '_' + 'temp')
        return_temp_h = model.find_component(heat_input[1] + '_' +
                                             heat_input[0] + '_' + 'temp')
        heat_output = self.heat_flows_out[0]
        temp_c = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                      '_' + 'temp')
        return_temp_c = model.find_component(heat_output[0] + '_' +
                                             heat_output[1] + '_' + 'temp')

        delta_temp = model.find_component('delta_temp_' + self.name)
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        area = model.find_component('size_' + self.name)

        for t in range(len(model.time_step)):
            model.cons.add(delta_temp[t+1] == (temp_h[t+1] + return_temp_h[t+1]
                                               - temp_c[t+1] -
                                               return_temp_c[t+1]) / 2)
            model.cons.add(input_energy[t+1] == self.k * area * delta_temp[t+1])

    def add_cons(self, model):
        self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        self._constraint_mass_flow(model)
        self._constraint_loss(model)
        self._constraint_delta_temp(model)
        self._constraint_maxpower(model)
        self._constraint_vdi2067(model)
        # self._constraint_conver(model)
        # todo this one should not exist in this class, should think, if it
        #  causes problem by FluidComponent child.

    def add_vars(self, model):
        super().add_vars(model)

        # # These temperature variables and mass flow variables represent the
        # # variable of high temperature side. In haus station is the network
        # # side.
        # temp_h = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('temp_h_' + self.name, temp_h)
        #
        # return_temp_h = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('return_temp_h_' + self.name, return_temp_h)
        #
        # mass_flow_h = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('mass_flow_h_' + self.name, mass_flow_h)
        #
        # # These temperature variables and mass flow variables represent the
        # # variable of low temperature side. which represent haus side in haus
        # # station.
        # temp_c = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('temp_c_' + self.name, temp_c)
        #
        # return_temp_c = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('return_temp_c_' + self.name, return_temp_c)
        #
        # mass_flow_c = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('mass_flow_c_' + self.name, mass_flow_c)

        # Temperature difference value
        delta_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('delta_temp_' + self.name, delta_temp)

        # The energy loss is considered, because of the heat transfer to the
        # environment.
        loss = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('loss_' + self.name, loss)
