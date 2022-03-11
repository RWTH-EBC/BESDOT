from scripts.Component import Component
import os
import warnings

import pandas as pd
import pyomo.environ as pyo


class ElectricityGrid(Component):

    def __init__(self, comp_name, comp_type="ElectricityGrid", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['elec']
        self.outputs = ['elec']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_conver(self, model):
        """
        The Grid has "no" fixed input and therefore it should not be constrainted
        """
        pass

    # todo (qli): building.py anpassen
    def _constraint_elec_balance(self, model):
        buy_elec = model.find_component('output_elec_' + self.name)
        # todo (qli): Name anpassen ('chp_big_' + self.name + '_elec')
        # energy_flow_elec_input = model.find_component(
        #     'chp_small_' + self.name + '_elec')
        energy_flow_elec_output = model.find_component(self.name + '_e_boi')
        for t in model.time_step:
            # model.cons.add(sell_elec[t] == energy_flow_elec_input[t])
            model.cons.add(buy_elec[t] == energy_flow_elec_output[t])

    # todo (qli): building.py anpassen
    def add_cons(self, model):
        self._constraint_elec_balance(model)

    def add_vars(self, model):
        super().add_vars(model)

        # sell_elec = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('input_elec_' + self.name, sell_elec)
        #
        # buy_elec = pyo.Var(model.time_step, bounds=(0, None))
        # model.add_component('output_elec_' + self.name, buy_elec)

