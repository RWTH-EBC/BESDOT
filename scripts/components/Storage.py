import warnings
import pyomo.environ as pyo
import scripts
import math
from scripts.Component import Component


class Storage(Component):

    def __init__(self, comp_name, comp_type="Storage", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

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
            # todo: Attention!! The efficiency is assumed with 100% in the
            #  following constraint. Should be checked again or modified.
            model.cons.add(stored_energy[t+1] + input_energy[t+1] -
                           output_energy[t+1] == stored_energy[t+2])

        # Attention! The initial soc of storage is hard coded. for
        # further development should notice this. And the end soc is not
        # set, which is not so important.
        model.cons.add(stored_energy[1] == 0)

    def _constraint_maxpower(self, model):
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        size = model.find_component('size_' + self.name)

        # todo: the efficiency for input and output process?
        for t in model.time_step:
            model.cons.add(input_energy[t] <= size / self.e2p_in)
            model.cons.add(output_energy[t] <= size / self.e2p_out)

    def _constraint_maxcap(self, model):
        stored_energy = model.find_component('energy_' + self.name)
        size = model.find_component('size_' + self.name)

        for t in model.time_step:
            model.cons.add(stored_energy[t] <= self.max_soc * size)
            model.cons.add(stored_energy[t] >= self.min_soc * size)

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_maxpower(model)
        self._constraint_maxcap(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        """
        Compared to the general variables in components, the following
        variable should be assigned:
            energy: stored energy in the storage in each time step
        """
        super().add_vars(model)

        energy = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('energy_' + self.name, energy)
