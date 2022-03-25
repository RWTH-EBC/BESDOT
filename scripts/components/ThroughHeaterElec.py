import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent


class ThroughHeaterElec(FluidComponent):
    """
    todo add description
    """

    def __init__(self, comp_name, comp_type="ThroughHeaterElec",
                 comp_model=None, min_size=0, max_size=1000, current_size=0):
        self.inputs = ['heat', 'elec']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_conver(self, model):
        input_heat = model.find_component('input_heat_' + self.name)
        input_elec = model.find_component('input_elec_' + self.name)
        output_energy = model.find_component('output_heat_' + self.name)

        for t in model.time_step:
            model.cons.add(output_energy[t] == input_elec[t] *
                           self.efficiency['heat'] + input_heat[t])

    def constraint_sum_inputs(self, model, energy_type, energy_flows):
        """
        For ThroughHeaterElec object the energy input in type 'heat' could not
        be seen as real input, only electricity, which is converted into heat,
        could be seen as input.
        Args:
            model: pyomo model object
            other_comp: pandas Series, taken from building topology
            energy_type: modeled energy type in case of more than 1 input type
            energy_flows: the energy flows from building object, dict
            comp_obj: the component objects in building, might be used by the
                spacial components, dict
        Returns: None
        """
        # Search connected component from other_comp
        input_flows = []
        for flow in energy_flows[energy_type]:
            if flow[1] == self.name:
                input_flows.append(flow)
        input_energy = model.find_component('input_' + energy_type + '_' +
                                            self.name)

        # # Divide input components into elec and heat type
        # elec_components = []
        # heat_components = []
        # for comp in input_components:
        #     # The reason for checking 'heat' instead of 'elec' is that, assume
        #     # if CHP provide energy to this component, the provided energy is
        #     # heat. If the opposite scenario need to be considered, this part
        #     # should be checked and modified.
        #     if 'heat' in comp_obj[comp].outputs:
        #         heat_components.append(comp)
        #     else:
        #         elec_components.append(comp)

        # if energy_type == 'elec':
        #     for t in model.time_step:
        #         model.cons.add(input_energy[t] == sum(
        #             energy_flow[(input_comp, self.name)][t] for input_comp in
        #             elec_components))
        # elif energy_type == 'heat':
        #     for t in model.time_step:
        #         model.cons.add(input_energy[t] == sum(
        #             energy_flow[(input_comp, self.name)][t] for input_comp in
        #             heat_components))

        for t in model.time_step:
            model.cons.add(input_energy[t] == sum(
                energy_flows[energy_type][flow][t] for flow in input_flows))

    def _constraint_virtual(self, model):
        """Similar to HeatExchangerFluid, as virtual model to the actual
        device, the mass flow of input side and output side should be same.
        TODO: attention! in the developed case, in both input and output side
         only a stream of water is considered. More than one stream should be
         developed later. Or it only allow one input and output? This could also
         influence the constraint of sum inputs slightly. """
        mass_flow_in = False
        temp_flow_in = False
        mass_flow_out = False
        temp_flow_out = False

        for energy_flow_in in self.energy_flows['input']['heat']:
            if energy_flow_in in self.heat_flows_in:
                mass_flow_in = model.find_component(energy_flow_in[0] + '_' +
                                                    energy_flow_in[1] + '_mass')
                temp_flow_in = model.find_component(energy_flow_in[1] + '_' +
                                                    energy_flow_in[0] + '_temp')
        for energy_flow_out in self.energy_flows['output']['heat']:
            if energy_flow_out in self.heat_flows_out:
                mass_flow_out = model.find_component(energy_flow_out[0] + '_' +
                                                     energy_flow_out[
                                                         1] + '_mass')
                temp_flow_out = model.find_component(energy_flow_out[1] + '_' +
                                                     energy_flow_out[
                                                         0] + '_temp')

        # Temperature from consumption to ThroughHeaterElec should be equal to the
        # temperature from ThroughHeaterElec to other components.
        if mass_flow_in and temp_flow_in and mass_flow_out and temp_flow_out:
            for t in model.time_step:
                model.cons.add(mass_flow_in[t] == mass_flow_out[t])
                model.cons.add(temp_flow_in[t] == temp_flow_out[t])
        else:
            warnings.warn("Can't find heat flows in " + self.name)

    def add_cons(self, model):
        self._constraint_heat_inputs(model)
        self._constraint_heat_outputs(model)
        self._constraint_conver(model)
        self._constraint_maxpower(model)
        self._constraint_vdi2067(model)
        self._constraint_virtual(model)

    def add_vars(self, model):
        super().add_vars(model)
    #
    #     input_heat = pyo.Var(model.time_step, bounds=(0, None))
    #     model.add_component('input_heat_' + self.name, input_heat)
    #
    #     input_elec = pyo.Var(model.time_step, bounds=(0, None))
    #     model.add_component('input_elec_' + self.name, input_elec)
    #
    #     output_energy = pyo.Var(model.time_step, bounds=(0, None))
    #     model.add_component('output_heat_' + self.name, output_energy)


