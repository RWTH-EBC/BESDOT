import pyomo.environ as pyo


class Subsidy(object):
    """
    The subsidies for each energy device in building.
    ------------------------------------------------
    enact_year: the year, in which the regulation was enacted.
    version: In case some regulation have multiple version in a year,
     a secondary attribute 'version' is added. default set None
    components: the list of all subsidized device class.
    type: the type could be set as 'purchase' or 'operate'
    """
    def __init__(self, enact_year, version=None):
        self.name = 'Subsidy'
        self.enact_year = enact_year
        self.version = version
        self.components = []
        self.type = None

    def add_vars(self, model):
        # The subsidy for PV in EEG is for generated energy, so the subsidies
        # is added to each time step.
        for component in self.components:
            subsides = pyo.Var(bounds=(0, 10 ** 10))
            model.add_component('subsidy_' + self.name + '_' + component, subsides)
