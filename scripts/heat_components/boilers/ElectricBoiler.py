from component_library.component_models.BaseComponent \
    import BaseComponent


class ElectricBoiler(BaseComponent):

    def __init__(self, comp_name, min_size, max_size, current_size, properties):
        super().__init__(comp_name=comp_name,
                         commodity_1="electricity",
                         commodity_2="heat",
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         comp_type="ElectricBoiler",
                         properties=properties)
