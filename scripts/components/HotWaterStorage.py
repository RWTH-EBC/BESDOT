from scripts.components.Storage import Storage
from scripts.FluidComponent import FluidComponent


class HotWaterStorage(Storage):
    def __init__(self, comp_name, comp_type="HotWaterStorage",
                 comp_model=None, min_size=0, max_size=1000, current_size=0):
        self.inputs = ['heat']
        self.outputs = ['heat']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_unchanged_periode(self, model, aggregation):
        """This constraint is used for the situation, in which the temporal
        clustering method is considered. The classical method to model the
        storage soc assumes, that the soc remains the same at the beginning
        and end of the period. This is not suitable for seasonal storage,
        but acceptable in the buildings with small storage."""


