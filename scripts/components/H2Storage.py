from scripts.components.Storage import Storage

small_num = 0.0001


class H2Storage(Storage):

    def __init__(self, comp_name, comp_type="H2Storage", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['hydrogen']
        self.outputs = ['hydrogen']

        self.set_init = True

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
