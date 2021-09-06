from component_library.component_models.BaseComponent \
    import BaseComponent


class UnderfloorHeat(BaseComponent):
    """
    pass
    """
    def __init__(self, comp_name, min_size, max_size, current_size, properties):
        super().__init__(comp_name=comp_name,
                         commodity_1="heat",
                         commodity_2="heat",
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         comp_type="UnderfloorHeat",
                         properties=properties)

