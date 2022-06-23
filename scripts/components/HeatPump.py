import pyomo.environ as pyo
from scripts.Component import Component


class HeatPump(Component):

    def __init__(self, comp_name, temp_profile, comp_type="HeatPump",
                 comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        # Define inputs and outputs before the initialisation of component,
        # otherwise we can't read properties properly. By getting efficiency,
        # the energy typ is needed.
        self.inputs = ['elec']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.temp_profile = temp_profile
        # self.cop = list(map(self.calc_cop, self.temp_profile))

    def _constraint_cop(self, model, temp_profile):
        """
        Calculate the COP value in each time step, with default set
        temperature of 60 degree and machine efficiency of 40%.
        """
        cop = model.find_component('cop_' + self.name)
        temp_var = model.find_component('temp_' + self.name)
        for t in model.time_step:
            #todo:qli
            #model.cons.add(cop[t] * (temp_var[t] - temp_profile[t - 1]) == (
                    #temp_var[t] + 273.15) * self.efficiency[self.outputs[0]])
            model.cons.add(cop[t] * (temp_var - temp_profile[t - 1]) == (
                    temp_var + 273.15) * self.efficiency[self.outputs[0]])

    def _constraint_conver(self, model):
        """
        Energy conservation equation for heat pump with variable COP value.
        Heat pump has only one input and one output, maybe? be caution for 5
        generation heat network.
        """
        cop = model.find_component('cop_' + self.name)
        input_powers = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        output_powers = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)

        for t in model.time_step:
            # index in pyomo model and python list is different
            model.cons.add(output_powers[t] == input_powers[t] * cop[t])

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_cop(model, self.temp_profile)
        self._constraint_vdi2067(model)
        self._constraint_maxpower(model)

    def add_vars(self, model):
        super().add_vars(model)

        #todo:qli
        #temp = pyo.Var(model.time_step, bounds=(0, None))
        #model.add_component('temp_' + self.name, temp)
        temp = pyo.Var(bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        cop = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('cop_' + self.name, cop)


