import pyomo.environ as pyo
from scripts.Component import Component


class HeatPump(Component):

    def __init__(self, comp_name, temp_profile, comp_type="HeatPump",
                 comp_model=None):
        # Define inputs and outputs before the initialisation of component,
        # otherwise we can't read properties properly. By getting efficiency,
        # the energy typ is needed.
        self.inputs = ['elec']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)

        self.temp_profile = temp_profile
        self.cop = list(map(self.calc_cop, self.temp_profile))

    def calc_cop(self, amb_t, set_t=60):
        """
        Calculate the COP value in each time step, with default set
        temperature of 60 degree and machine efficiency of 40%.
        """
        cop = (set_t + 273.15) / (set_t - amb_t) * self.efficiency[
            self.outputs[0]]
        return cop

    def _constraint_conver(self, model):
        """
        Energy conservation equation for heat pump with variable COP value.
        Heat pump has only one input and one output, maybe? be caution for 5
        generation heat network.
        """
        input_powers = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        output_powers = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)

        for t in model.time_step:
            # index in pyomo model and python list is different
            model.cons.add(output_powers[t] == input_powers[t] * self.cop[t-1])
