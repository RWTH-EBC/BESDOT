"""
Heat outlet is the component, which is used to connect the heat provider to
the heat grid or other heat consumers.
This component has no investment cost and no max. power constraint.
Most buildings do not have heat outlet, but the energy hub has heat outlet.
"""
from scripts.Component import Component


class HeatOutlet(Component):

    def __init__(self, comp_name, comp_type="HeatOutlet", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.heat_profile = []

    def _read_properties(self, properties):
        """
        The component heat outlet is a virtual component anc the component has
        an efficiency of 1.
        """
        if not hasattr(self, 'efficiency'):
            self.efficiency = 1

    def update_profile(self, demand_profile):
        self.heat_profile = demand_profile

    def _constraint_vdi2067(self, model):
        """
        The heat consumption has currently no max. power or investment
        constraint.
        """
        pass

    def _constraint_maxpower(self, model):
        """
        The heat consumption has currently no max. power or investment
        constraint.
        """
        pass

    def _constraint_conver(self, model):
        """The input energy for Consumption should equal to the demand
        profile."""
        input_energy = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        for t in model.time_step:
            # ATTENTION!!! The time_step in pyomo is from 1 to 8760 and
            # python list is from 0 to 8759, so the index should be modified.
            model.cons.add(input_energy[t] == self.heat_profile[t-1])



