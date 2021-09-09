import warnings
import pyomo.environ as pyo
import scripts
import math
from scripts.Component import Component


class Storage(Component):

    def __init__(self, comp_name, comp_type="Storage", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if hasattr(self, 'efficiency'):
            delattr(self, 'efficiency')  # delete the attribute 'efficiency'
        if 'input efficiency' in properties.columns:
            self.input_efficiency = float(properties['input efficiency'])
        elif 'input_efficiency' in properties.columns:
            self.input_efficiency = float(properties['input_efficiency'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for input efficiency.")
        if 'output efficiency' in properties.columns:
            self.output_efficiency = float(properties['output efficiency'])
        elif 'output_efficiency' in properties.columns:
            self.output_efficiency = float(properties['output_efficiency'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for output efficiency.")
        if 'max soc' in properties.columns:
            self.max_soc = float(properties['max soc'])
        elif 'max_soc' in properties.columns:
            self.max_soc = float(properties['max_soc'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for max soc.")
        if 'min soc' in properties.columns:
            self.min_soc = float(properties['min soc'])
        elif 'min_soc' in properties.columns:
            self.min_soc = float(properties['min_soc'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for min soc.")
        if 'init soc' in properties.columns:
            self.init_soc = float(properties['init soc'])
        elif 'init_soc' in properties.columns:
            self.init_soc = float(properties['init_soc'])
        else:
            self.init_soc = 0.5
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for init soc. init soc has been set to be 0.5.")
        if 'e2p in' in properties.columns:
            self.e2p_in = float(properties['e2p in'])
        elif 'e2p_in' in properties.columns:
            self.e2p_in = float(properties['e2p_in'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for e2p in.")
        if 'e2p out' in properties.columns:
            self.e2p_out = float(properties['e2p out'])
        elif 'e2p_out' in properties.columns:
            self.e2p_out = float(properties['e2p_out'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for e2p out.")

    def _constraint_conver(self, model):
        """Energy conservation equation for storage, in storage could only
        a kind of energy could be stored. so self.inputs and self.outputs
        have only one item.
        Attention: It is not easy to define the stored energy at each time
        step. Other energy flows happen in the time step (1 hour), but stored
        energy is a state, which varies before and after the time step. In
        this tools, we consider the stored energy is before the time step.
        """
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        stored_energy = model.find_component('energy_' + self.name)

        for t in range(len(model.time_step)-1):
            model.cons.add(stored_energy[t+1] + input_energy[t+1] -
                           output_energy[t+1] == stored_energy[t+2])

        # Attention! The initial soc of storage is hard coded. for
        # further development should notice this. And the end soc is not
        # set, which is not so important.
        model.cons.add(stored_energy[1] == 0)

    def _constraint_maxpower(self, model, flows, var_dict, T):
        input_powers = flows[self.input_energy][self.name][0]
        output_powers = flows[self.output_energy][self.name][1]

        # todo: discuss, if we need to consider efficiency for input
        for t in T:
            model.cons.add(
                pyo.quicksum(var_dict[i][t] * self.input_efficiency for i in input_powers)
                <= var_dict[('cap', self.name)] / self.e2p_in)
            # model.cons.add(
            #     pyo.quicksum(var_dict[i][t] * self.input_efficiency for i in
            #                  input_powers) <= self.max_input)
            model.cons.add(
                pyo.quicksum(var_dict[i][t] / self.output_efficiency for i in output_powers)
                <= var_dict[('cap', self.name)] / self.e2p_out)

    def _constraint_maxcap(self, model, var_dict, T):
        for t in T:
            model.cons.add(var_dict[('energy', self.name)][t] <= self.max_soc *
                           var_dict[('cap', self.name)])
            model.cons.add(var_dict[('energy', self.name)][t] >= self.min_soc *
                           var_dict[('cap', self.name)])

    def _constraint_vdi2067(self, model, var_dict, T):
        annual_cost = scripts.calc_annuity_vdi2067.run(T, self.life, self.cost, var_dict[('cap', self.name)],
                                                       self.f_inst, self.f_w,
                                                       self.f_op, model)
        model.cons.add(var_dict[('annual_cost', self.name)] == annual_cost)

    def add_all_constr(self, model, flows, var_dict, T):
        self._constraint_conver(model)
        self._constraint_maxpower(model, flows, var_dict, T)
        self._constraint_maxcap(model, var_dict, T)
        self._constraint_vdi2067(model, var_dict, T)

    def add_vars(self, model):
        """
        Compared to the general variables in components, the following
        variable should be assigned:
            energy: stored energy in the storage in each time step
        """
        super().add_vars(model)

        energy = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('energy_' + self.name, energy)
