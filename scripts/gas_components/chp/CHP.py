from component_library.component_models.BaseComponent \
    import BaseComponent


class CHP(BaseComponent):

    def __init__(self, comp_name, min_size, max_size, current_size, properties):
        super().__init__(comp_name=comp_name,
                         commodity_1="gas",
                         commodity_2="heat",
                         commodity_3="elec_ac",
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         comp_type="CHP",
                         properties=properties)
