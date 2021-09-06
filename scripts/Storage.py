import warnings
import pyomo.environ as pyo
import scripts
import math
from component_library.component_models.BaseComponent \
    import BaseComponent


class BaseStorage(BaseComponent):

    def __init__(self, comp_name, commodity, min_size, max_size, current_size, comp_type="BaseStorage",
                 properties=None):
        super().__init__(comp_name=comp_name,
                         commodity_1=commodity,
                         commodity_2=commodity,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         comp_type=comp_type,
                         properties=properties)

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

    def _constraint_conser(self, model, flows, var_dict, T):
        """Energy conservation equation for storage"""
        # todo jgn: the time steps should be individually for each iteration calculated
        #  if variable time steps are implemented
        time_step = T[1]-T[0]
        time_step = time_step.seconds/3600  # time step in [h]
        input_powers = flows[self.input_energy][self.name][0]
        output_powers = flows[self.output_energy][self.name][1]

        model.cons.add(var_dict[('energy', self.name)][T[0]] ==
                       var_dict[('init_soc', self.name)] * var_dict[('cap', self.name)]
                       + pyo.quicksum(var_dict[i][T[0]] * self.input_efficiency * time_step for i in input_powers)
                       - pyo.quicksum(var_dict[i][T[0]] / self.output_efficiency * time_step for i in output_powers))

        for t in range(len(T)-1):
            # print(t)
            model.cons.add(
                var_dict[('energy', self.name)][T[t+1]] == var_dict[('energy', self.name)][T[t]]
                + pyo.quicksum(var_dict[i][T[t+1]] * self.input_efficiency * time_step for i in input_powers) -
                pyo.quicksum(var_dict[i][T[t+1]] / self.output_efficiency * time_step for i in output_powers))

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
        self._constraint_conser(model, flows, var_dict, T)
        self._constraint_maxpower(model, flows, var_dict, T)
        self._constraint_maxcap(model, var_dict, T)
        self._constraint_vdi2067(model, var_dict, T)

    def add_variables(self, input_profiles, plant_parameters, var_dict, flows,
                      model, T):
        var_dict[self.name] = {}
        # todo jgn: replace the lower and upper boundary of capacity with
        #  max. min capacity in the input matrix
        lb_cap, ub_cap = [self.min_size, self.max_size]
        if math.isinf(lb_cap):
            lb_cap = None
        if math.isinf(ub_cap):
            ub_cap = None
        var_dict[('cap', self.name)] = pyo.Var(bounds=(lb_cap, ub_cap))
        model.add_component('cap_' + self.name, var_dict[('cap', self.name)])
        var_dict[('annual_cost', self.name)] = pyo.Var(bounds=(0, None))
        model.add_component('annual_cost' + self.name, var_dict[('annual_cost', self.name)])
        # The linking variables should be added if the bidirectional flows occur
        # around this component
        self._add_linking_variables(var_dict, flows, model, T)

        # todo: discuss about the initial soc and end soc of storage
        var_dict[('init_soc', self.name)] = self.init_soc
        # var_dict[self.name]['soc'] = {}
        var_dict[('energy', self.name)] = {}
        for t in T:
            var_dict[('energy', self.name)][t] = pyo.Var(bounds=(0, None))
            model.add_component(
                self.name + '_energy_' + "_%s" % t, var_dict[('energy', self.name)][t])
