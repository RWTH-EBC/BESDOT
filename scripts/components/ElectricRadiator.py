from scripts.Component import Component


class ElectricRadiator(Component):
    """
    The electrical radiator is the device, which could be installed as a hot
    water radiator for space heating. So this device is not designed to cover
    the hot water demand.
    """
    def __init__(self, comp_name):
        super().__init__(comp_name=comp_name)

