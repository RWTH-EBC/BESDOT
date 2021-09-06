class Environment(object):
    def __init__(self):
        # todo: the default value should be check with the aktuell data
        self.elec_price = 0.3  # €/kWh
        self.gas_price = 0.1  # €/kWh
        self.elec_emission = 397  # g/kWh
        self.gas_emission = 202  # g/kWh

        # Read the weather file in the directory "data"
        self.temp_profil = []
        self.wind_profil = []
        self.irr_profil = []
