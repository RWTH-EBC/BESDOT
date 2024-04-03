import os
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Component import Component

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

small_num = 0.0001


class BiomassBoiler(Component):
    def __init__(self, comp_name, comp_type="BiomassBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['biomass']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

        self.min_part_load = 0.25

    def set_min_part_load(self, new_min_part_load):
        """
        Set a new minimum part load for the component.
        :param new_min_part_load: The new minimum part load value to be set.
        """
        self.min_part_load = new_min_part_load

    def add_vars(self, model):
        super().add_vars(model)
        # The subsidy for PV in EEG is for generated energy, so the subsidies
        # is added to each time step.
        # total_subsidy = pyo.Var(bounds=(0, None))
        # model.add_component('total_subsidy_' + self.name, total_subsidy)

    def add_cons(self, model):
        """The minimum part-load ratio is set for biomass boiler."""
        super().add_cons(model)
        self._constraint_part_load(model)

    def _constraint_part_load(self, model):
        """The part-load constraint of the boiler."""
        model.not_work_state = Disjunct(model.time_step)
        model.work_state = Disjunct(model.time_step)
        model.work_or_not = Disjunction(model.time_step)

        output_heat = model.find_component('output_heat_' + self.name)
        size = model.find_component('size_' + self.name)

        for t in model.time_step:
            @model.not_work_state[t].Constraint()
            def not_working(m):
                return output_heat[t] == 0

            @model.work_state[t].Constraint()
            def working(m):
                return output_heat[t] >= size * self.min_part_load

            model.work_or_not[t] = [model.not_work_state[t],
                                    model.work_state[t]]
