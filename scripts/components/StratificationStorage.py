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


class StratificationStorage(Storage):
    def __init__(self, comp_name, comp_type="StratificationStorage",
                 comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)

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

    def _constraint_conver(self, model, flows, var_dict, T):
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

        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        size = model.find_component('size_' + self.name)

        temp_var = model.find_component('temp_' + self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)
        loss_var = model.find_component('loss_' + self.name)
        mass_flow_var = model.find_component('mass_flow_' + self.name)

        model.cons.add(size == 100)

        for t in range(len(model.time_step)-1):
            model.cons.add((temp_var[t + 1] - temp_var[t]) * water_density *
                           size * water_heat_cap / unit_switch ==
                           (return_temp_var[t + 1] - temp_var[t + 1]) *
                           mass_flow_var[t + 1] * water_heat_cap / unit_switch -
                           loss_var[t + 1] + input_energy[t + 1])
            model.cons.add(output_energy[t + 1] ==
                           (temp_var[t + 1] - return_temp_var[t + 1]) *
                           mass_flow_var[t + 1] * water_heat_cap / unit_switch)
            # FIXME: The energy loss equation shouldn't be like the following
            #  format, which is only used for validation.
            model.cons.add(loss_var[t+1] == 1.5 * ((temp_var[t+1] - 20) / 1000))

    def _constraint_temp(self, model):
        # Initial temperature for water in storage is define with a constant
        # value, maybe later could change to others, like air temperature at
        # time step 0.
        temp_var = model.find_component('temp_' + self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)
        loss_var = model.find_component('loss_' + self.name)

        model.cons.add(temp_var[1] == 60)
        # model.cons.add(return_temp_var[1] == 20)
        model.cons.add(loss_var[1] == 0)

        for t in model.time_step:
            model.cons.add(temp_var[t] <= self.max_temp)
            # model.cons.add(temp_var[t] >= self.min_temp)
            model.cons.add(return_temp_var[t] <= self.max_temp)
            # model.cons.add(return_temp_var[t] >= self.min_temp)

    def _constraint_return_temp(self, model):
        # The first constraint for return temperature. Assuming a constant
        # temperature difference between flow temperature and return
        # temperature.
        delta_temp = 20  # unit K
        min_delta_temp = 0
        temp_var = model.find_component('temp_' + self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)

        for t in model.time_step:
            model.cons.add(temp_var[t] - return_temp_var[t] <= delta_temp)
            model.cons.add(temp_var[t] - return_temp_var[t] >= min_delta_temp)

    def _constraint_mass_flow(self, model):
        # The mass flow set to be constant as circulation pumps
        mass_flow = 100  # unit kg/h
        mass_flow_var = model.find_component('mass_flow_' + self.name)
        for t in model.time_step:
            model.cons.add(mass_flow_var[t] == mass_flow)

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_temp(model)
        self._constraint_return_temp(model)
        self._constraint_mass_flow(model)
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
