import pyomo.environ as pyo
from scripts.Component import Component
import warnings

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class GasBoiler(Component):
    def __init__(self, comp_name, comp_type="GasBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['gas']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def get_properties(self, model):
        model_property_file = os.path.join(base_path, 'data',
                                           'component_database',
                                           'GasBoiler',
                                           'BOI1_exhaust_gas_loss.csv')
        properties = pd.read_csv(model_property_file)
        return properties

    def _read_properties(self, properties):
        if 'exhaustgasloss' in properties.columns:
            self.exhaustgasloss = float(properties['exhaustgasloss'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for exhaust gas loss.")



