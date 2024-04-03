from scripts.Component import Component
import os

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

small_num = 0.0001


class Electrolyzer(Component):
    def __init__(self, comp_name, comp_type="Electrolyzer", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['elec']
        self.outputs = ['hydrogen']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
