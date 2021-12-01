import pyomo.environ as pyo
from scripts.components.GasBoiler import GasBoiler
import warnings

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class CondensingBoiler(GasBoiler):
    def __init__(self, comp_name, comp_type="CondensingBoiler", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

