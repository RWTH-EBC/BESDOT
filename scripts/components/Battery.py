import pyomo.environ as pyo
from scripts.Storage import Storage
import warnings


class Battery(Storage):

    def __init__(self, comp_name):
        super().__init__(comp_name=comp_name)

    def _read_properties(self, properties):
        """
        The LIB needs additionally the cycle life to calculate the cycling ageing
        """
        super()._read_properties(properties)
        if 'cycle life' in properties.columns:
            self.cycle_life = int(properties['cycle life'])
        elif 'cycle_life' in properties.columns:
            self.cycle_life = int(properties['cycle_life'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for cycle life.")
        if 'start cycle' in properties.columns:
            self.start_cycle = int(properties['start cycle'])
        elif 'start_cycle' in properties.columns:
            self.start_cycle = int(properties['start_cycle'])
        else:
            self.start_cycle = 0
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for start cycle. The start cycle is set to be 0.")

    def add_variables(self, input_parameters, plant_parameters, var_dict, flows, model, T):
        super().add_variables(input_parameters, plant_parameters, var_dict, flows, model, T)
        self._add_cycle_variables(plant_parameters, var_dict, model, T)

    def add_all_constr(self, model, flows, var_dict, T):
        super().add_all_constr(model, flows, var_dict, T)
        self._cycle_constraints(model, flows, var_dict, T)

    def _calculate_aging_factor(self):
        aging_f = 0.8 ** (1 / self.cycle_life)
        return aging_f

    def _add_cycle_variables(self, plant_parameters, var_dict, model, T):
        # we save the calculated aging factor in the plant parameters dict for later use in BaseProsumer
        plant_parameters[(self.name, self.component_type)]['aging_factor'] = self._calculate_aging_factor()

        # create the cumulative cycle variables
        var_dict[('cum_cycle', self.name)] = {}
        for t in T:
            var_dict[('cum_cycle', self.name)][t] = pyo.Var(bounds=(0, None))
            model.add_component('cum_cycle' + '_' + self.name + "_%s" % t,
                                var_dict[('cum_cycle', self.name)][t])

        # get the current starting state of battery cycling
        # Assign starting energy value in the var_dict
        var_dict[('cycle_0', self.name)] = self.start_cycle

    # Todo: adapt energy calculations when changing resolution to 15min
    def _cycle_constraints(self, model, flows, var_dict, T):
        # find out the component in flow dictionary according to name
        input_powers = flows['electricity'][self.name][0]
        output_powers = flows['electricity'][self.name][1]
        # Add cumulative cycles constraints, counting equivalent full cycles relative to the real size of the battery
        for t in range(len(T)-1):
            model.cons.add(
                var_dict[('cum_cycle', self.name)][T[t+1]] == var_dict[('cum_cycle', self.name)][T[t]] + (
                    pyo.quicksum(var_dict[i][t] * self.input_efficiency for i in input_powers) + pyo.quicksum(
                        var_dict[i][t] / self.output_efficiency for i in output_powers)) / 2 / var_dict[('cap', self.name)])
        # Add the cycling ageing for the t = 0
        model.cons.add(var_dict[('cum_cycle', self.name)][T[0]] == var_dict[('cycle_0', self.name)])

    # todo jgn: the implementation of real cycling ageing hasn't been done yet!!



