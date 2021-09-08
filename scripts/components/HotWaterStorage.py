from scripts.Storage import Storage


class HotWaterStorage(Storage):
    def __init__(self, comp_name):
        super().__init__(comp_name=comp_name)
