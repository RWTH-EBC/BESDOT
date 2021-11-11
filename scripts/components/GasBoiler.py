import pyomo.environ as pyo
from scripts.Component import Component


class GasBoiler(Component):
    def __init__(self, comp_name, comp_type="GasBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['gas']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

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
        return_temp_var = model.find_component('return_temp_' + self.name)
        loss_var = model.find_component('loss_' + self.name)
        mass_flow_var = model.find_component('mass_flow_' + self.name)

        for t in range(len(model.time_step)):
            model.cons.add(output_energy[t+1] ==
                           (temp_var[t+1] - return_temp_var[t+1]) *
                           mass_flow_var[t+1] * water_heat_cap / unit_switch)
            model.cons.add(output_energy[t+1] == size)

    def _constraint_loss(self, model):
        pass

    def _constraint_temp(self, model, init_temp=80):
        # Initial temperature for water in storage is define with a constant
        # value.
        temp_var = model.find_component('temp_' + self.name)
        for t in model.time_step:
            model.cons.add(temp_var[t] == init_temp)

    def _constraint_return_temp(self, model, init_return_temp=60):
        # The first constraint for return temperature. Assuming a constant
        # temperature difference between flow temperature and return
        # temperature.
        return_temp_var = model.find_component('return_temp_' + self.name)
        for t in model.time_step:
            model.cons.add(return_temp_var[t] == init_return_temp)

    def add_cons(self, model):
        self._constraint_conver(model)
        #self._constraint_loss(model, loss_type='off')
        self._constraint_temp(model)
        self._constraint_return_temp(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)

        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        return_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('return_temp_' + self.name, return_temp)

        mass_flow = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('mass_flow_' + self.name, mass_flow)

        loss = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('loss_' + self.name, loss)