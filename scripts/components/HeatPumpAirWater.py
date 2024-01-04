"""
This code is inherited from the parent class HeatPump. It inherits
all properties and methods from the HeatPump class. Its purpose is to
distinguish, when modifying the topology CSV file, whether the comp_name
associated with comp_type HeatPump is "air_water_heat_pump". Currently,
this approach is being used, with the possibility of exploring better methods
in the future.
"""

from scripts.components.HeatPump import HeatPump


class HeatPumpAirWater(HeatPump):
    def __init__(self, comp_name, temp_profile, comp_type="HeatPumpAirWater",
                 comp_model=None,
                 min_size=0, max_size=1000, current_size=0):

        super().__init__(comp_name=comp_name,
                         temp_profile=temp_profile,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
