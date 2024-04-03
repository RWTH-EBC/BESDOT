import pyomo.environ as pyo
from scripts.Component import Component


class HeatGrid(Component):

    def __init__(self, comp_name, comp_type="HeatGrid", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        self.source_profile = None

    def add_source(self, source):
        """
        Add a source to the heat grid, which represents the upper limit of
        the source.
        """
        self.source_profile = source

    def _constraint_conver(self, model):
        """
        The Grid has "no" fixed input and therefore it should not be constrainted
        """
        pass

    def _constraint_maxpower(self, model):
        """
        The Grid could not provide more power than the source
        """
        if self.source_profile is not None:
            output_powers = model.find_component('output_heat_' + self.name)
            for t in model.time_step:
                model.cons.add(output_powers[t] <= self.source_profile[t-1])