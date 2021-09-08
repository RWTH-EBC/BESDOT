import pyomo.environ as pyo
from scripts.Component import Component


class HeatPump(Component):

    def __init__(self, comp_name, temp_profile, comp_type="HeatPump",
                 comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['elec']
        self.outputs = ['heat']
        self.temp_profile = temp_profile

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
