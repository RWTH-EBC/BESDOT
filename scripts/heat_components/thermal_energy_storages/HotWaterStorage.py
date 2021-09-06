from component_library.component_models.BaseStorage \
    import BaseStorage


class HotWaterStorage(BaseStorage):
    def __init__(self, comp_name, min_size, max_size, current_size, properties):
        super().__init__(comp_name=comp_name,
                         commodity="heat",
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         comp_type="HotWaterStorage",
                         properties=properties)
