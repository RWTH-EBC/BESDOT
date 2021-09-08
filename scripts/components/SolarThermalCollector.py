from scripts.Component import Component


class SolarThermalCollector(Component):

    def __init__(self, comp_name, irr_profile,
                 comp_type="SolarThermalCollector", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['solar']
        self.outputs = ['heat']
        self.irr_profile = irr_profile
