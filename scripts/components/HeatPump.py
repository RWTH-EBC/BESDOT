import pyomo.environ as pyo
from scripts.Component import Component


class HeatPump(Component):

    def __init__(self, comp_name):
        super().__init__(comp_name=comp_name)

    def calc_cop(self, amb_t, set_t=60):
        """
        Calculate the COP value in each time step, with default set
        temperature of 40 degree and machine efficiency of 50%.
        """
        cop = (set_t + 273.15) / (set_t - amb_t) * self.efficiency
        return cop

    def _constraint_conser(self, model, flows, var_dict, T):
        """
        Energy conservation equation for heat pump with variable COP value.
        """
        input_powers = flows[self.input_energy][self.name][0]
        output_powers = flows[self.output_energy][self.name][1]

        for t in T:
            model.cons.add(pyo.quicksum(var_dict[i][t] for i in input_powers)
                           * var_dict[('COP', self.name)][t] ==
                           pyo.quicksum(var_dict[i][t] for i in output_powers))

    def add_variables(self, input_profiles, plant_parameters, var_dict, flows,
                      model, T):
        """
        Add the variables for COP in each time step
        """
        super().add_variables(input_profiles, plant_parameters, var_dict,
                              flows, model, T)

        var_dict[('COP', self.name)] = {}
        for t in T:
            var_dict[('COP', self.name)][t] = pyo.Var(bounds=(0, None))
            model.add_component(self.name + '_COP_' + "_%s" % t,
                                var_dict[('COP', self.name)][t])

            var_dict[('COP', self.name)][t] = \
                self.calc_cop(input_profiles['air_temperature'][t])
