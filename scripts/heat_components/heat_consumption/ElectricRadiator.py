from component_library.component_models.BaseComponent \
    import BaseComponent


class ElectricRadiator(BaseComponent):
    """
    The electrical radiator is the device, which could be installed as a hot
    water radiator for space heating. So this device is not designed to cover
    the hot water demand.
    """
    def __init__(self, comp_name, min_size, max_size, current_size, properties):
        super().__init__(comp_name=comp_name,
                         commodity_1="elec_ac",
                         commodity_2="heat",
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         comp_type="ElectricRadiator",
                         properties=properties)

