"""
The parent class for components, which considers the fluid properties, like
temperature and mass flow.
"""
import pyomo.environ as pyo
from scripts.Component import Component

# Common parameters
water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
water_density = 1000  # kg/m3
unit_switch = 3600 * 1000  # J/kWh


class FluidComponent(Component):
    """
    This class would not include add_vars() and add_cons(). It is not supposed
    to be called directly as a component but as a father for other fluid
    components.
    """

    def __init__(self, comp_name, comp_type="FuildComponent", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.heat_flows_in = []  # The element in list should be dict,
        # which includes the tuples, in which shows the the relevant
        # heat flow variables.
        self.heat_flows_out = []

    def add_heat_flows(self, bld_heat_flows):
        # check the building heat flows and select the tuples related to this
        # device to add into list heat_flows.
        for element in bld_heat_flows:
            if self.name == element[0]:
                self.heat_flows_out.append(element)
            if self.name == element[1]:
                self.heat_flows_in.append(element)

    def _constraint_heat_inputs(self, model):
        """
        Equation between energy input and related heat flows, which consists of
        temperature and mass flow.
        """
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)

        # analyze quantities of circulation for component.
        energy_flow = {}  # storage all the energy flows in every circulation
        for heat_input in self.heat_flows_in:
            m_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'mass')
            t_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
                                         '_' + 'temp')
            energy_flow[heat_input] = model.find_component(heat_input[0] + '_' +
                                                           heat_input[1])
            for t in range(len(model.time_step)):
                model.cons.add(energy_flow[heat_input][t + 1] ==
                               (m_in[t + 1] * t_in[t + 1] - m_out[t + 1] *
                                t_out[t + 1]) * water_heat_cap / unit_switch)
                model.cons.add(t_in[t + 1] >= t_out[t + 1])

        # sum all energy flow for input energy and output energy
        # for t in range(len(model.time_step)):
        #     model.cons.add(input_energy[t + 1] == sum(energy_flow[flow][t + 1]
        #                                               for flow in
        #                                               self.heat_flows_in))

    def _constraint_heat_outputs(self, model):
        """
        Equation between energy output and related heat flows, which consists of
        temperature and mass flow.
        """
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        energy_flow = {}
        for heat_output in self.heat_flows_out:
            m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'mass')
            t_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'temp')
            t_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'temp')
            energy_flow[heat_output] = model.find_component(heat_output[0] +
                                                            '_' +
                                                            heat_output[1])
            for t in range(len(model.time_step)):
                model.cons.add(energy_flow[heat_output][t + 1] ==
                               (m_out[t + 1] * t_out[t + 1] - m_in[t + 1] *
                                t_in[t + 1]) * water_heat_cap / unit_switch)
                model.cons.add(t_in[t + 1] <= t_out[t + 1])

        # for t in range(len(model.time_step)):
        #     model.cons.add(output_energy[t + 1] == sum(energy_flow[flow][t + 1]
        #                                                for flow in
        #                                                self.heat_flows_out))

    # def _constraint_mass_flow(self, model):
    #     # The mass flow is set to be constant as circulation pumps
    #     # mass flow unit kg/h
    #
    #     for heat_input in self.heat_flows_in:
    #         m_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
    #                                     '_' + 'mass')
    #         m_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
    #                                      '_' + 'mass')
    #         for t in range(len(model.time_step)):
    #             model.cons.add(m_in[t + 1] == m_out[t + 1])
    #
    #     for heat_output in self.heat_flows_out:
    #         m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
    #                                     '_' + 'mass')
    #         m_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
    #                                      '_' + 'mass')
    #         for t in range(len(model.time_step)):
    #             model.cons.add(m_in[t + 1] == m_out[t + 1])
