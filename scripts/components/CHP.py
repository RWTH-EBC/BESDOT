from scripts.Component import Component


class CHP(Component):

    def __init__(self, comp_name, comp_type="CHP", comp_model=None):
        self.inputs = ['gas']
        self.outputs = ['heat', 'elec']
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if 'el_efficiency' in properties.columns:
            self.efficiency['elec'] = float(properties['el_efficiency'])
        if 'th_efficiency' in properties.columns:
            self.efficiency['heat'] = float(properties['th_efficiency'])
