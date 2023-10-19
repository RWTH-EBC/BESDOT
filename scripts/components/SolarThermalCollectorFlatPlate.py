"""
This code is inherited from the parent class SolarThermalCollector. It
inherits all properties and methods from the SolarThermalCollector class.
Its purpose is to distinguish, when modifying the topology CSV file, whether
the comp_name associated with comp_type SolarThermalCollector is "flat_plate_solar_coll".
Currently, this approach is being used, with the possibility of exploring better methods
in the future.
"""

from scripts.components.SolarThermalCollector import SolarThermalCollector


class SolarThermalCollectorFlatPlate(SolarThermalCollector):
    def __init__(self, comp_name, temp_profile, irr_profile,
                 comp_type="SolarThermalCollectorFlatPlate", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):

        super().__init__(comp_name=comp_name,
                         temp_profile=temp_profile,
                         irr_profile=irr_profile,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
