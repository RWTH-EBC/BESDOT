from scripts.Storage import Storage


class HotWaterStorage(Storage):
    def __init__(self, comp_name, comp_type="HotWaterStorage", comp_model=None):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model)
        self.inputs = ['heat']
        self.outputs = ['heat']
