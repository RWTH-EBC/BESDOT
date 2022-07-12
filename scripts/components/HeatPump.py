import pyomo.environ as pyo
from scripts.Component import Component
import warnings

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

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if 'outlet temperature' in properties.columns:
            self.outlet_temp = float(properties['outlet temperature'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for outlet temperature.")
            self.outlet_temp = 50

        # self.set_temp = 55

    def _constraint_cop(self, model):
        """
        Calculate the COP value in each time step, with default set
        temperature of 60 degree and machine efficiency of 40%.
        Setting COP as Parameter instead of Variable could reduce the
        complexity of mathematical model. Even from non convex model into
        convex model.
        """
        # The cop_list could only be defined with dict, list is not possible
        # for pyomo 6.0. The reason is the unmatched index in pyomo and python
        cop_list = {}
        for t in model.time_step:
            cop_list[t] = (self.outlet_temp + 273.15) * self.efficiency[
                self.outputs[0]] / (self.outlet_temp - self.temp_profile[t - 1])

        cop = pyo.Param(model.time_step, initialize=cop_list)
        model.add_component('cop_' + self.name, cop)


    def _constraint_conver(self, model):
        """
        Energy conservation equation for heat pump with variable COP value.
        Heat pump has only one input and one output, maybe? be caution for 5
        generation heat network.
        """
        outlet_temp = model.find_component('outlet_temp_' + self.name)
        for heat_output in self.heat_flows_out:
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] + '_' + 'temp')
        input_powers = model.find_component('input_' + self.inputs[0] + '_' + self.name)
        output_powers = model.find_component('output_' + self.outputs[0] + '_' + self.name)
        cop = model.find_component('cop_' + self.name)
        #cop = 5 - 0.0928 * (self.outlet_temp - 35)
        for t in model.time_step:
            model.cons.add(cop[t] == 5 - 0.0928 * (t_out[t] - 35))
            model.cons.add(output_powers[t] == input_powers[t] * cop[t])
<<<<<<< scripts/components/HeatPump.py
            # model.cons.add(t_out[t] == self.outlet_temp)
            #model.cons.add(output_powers[t] == input_powers[t] * cop)
            model.cons.add(outlet_temp[t] == t_out[t])

    def add_vars(self, model):
        super().add_vars(model)

        cop = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('cop_' + self.name, cop)

        outlet_temp = pyo.Var(model.time_step, bounds=(30, 80))
        model.add_component('outlet_temp_' + self.name, outlet_temp)
=======

    def add_cons(self, model):
        self._constraint_cop(model)
        self._constraint_conver(model)
        self._constraint_vdi2067(model)
        self._constraint_maxpower(model)

    # def add_vars(self, model):
    #     """
    #     This method adds the pyomo variables and parameters
    #     """
    #     super().add_vars(model)
    #
    #     cop = pyo.Param(model.time_step, initialize=0)
    #     model.add_component('cop_' + self.name, cop)
>>>>>>> scripts/components/HeatPump.py
