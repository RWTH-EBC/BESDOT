"""
Simplified Modell for internal use.
"""

import pyomo.environ as pyo
from tools.gen_heat_profile import *
from tools.gen_elec_profile import gen_elec_profile
from tools import get_all_class

module_dict = get_all_class.run()


class Building(object):
    def __init__(self, name, area, bld_typ='Verwaltungsgebäude',
                 annual_heat_demand=None,
                 annual_elec_demand=None):
        """
        Initialization for building.
        :param name: name of the building, should be unique
        """
        self.name = name
        self.area = area
        self.building_typ = bld_typ
        # fixme: The building type is in German, which is connected with the
        #  script "gen_heat_profil" and needs tobe changed to English
        # todo: TEK provided only the value for non-residential building. For
        #  residential building should get the data from the project TABULA.

        # Calculate the annual energy demand for heating, hot water and
        # electricity. Using TEK Tools from IWU.
        self.annual_demand = {"elec_demand": 0,
                              "heat_demand": 0,
                              "cool_demand": 0,
                              "hot_water_demand": 0,
                              "gas_demand": 0}
        if annual_heat_demand is None:
            self.add_annual_demand('heat')
        if annual_elec_demand is None:
            self.add_annual_demand('elec')

        # The gas_demand is for natural gas, the demand of hydrogen is still not
        # considered in building. The profile of heat and cool demand depends
        # on the air temperature, which is define in the Environment object.
        # So the method for generate profiles should be called in project
        # rather than in building object.
        self.demand_profile = {"elec_demand": [],
                               "heat_demand": [],
                               "cool_demand": [],
                               "hot_water_demand": [],
                               "gas_demand": []}

        # The topology of the building energy system and all available
        # components in the system, which doesn't mean the components would
        # have to be choose by optimizer.
        self.topology = None
        self.components = {}

    def add_annual_demand(self, energy_sector):
        """Calculate the annual heat demand according to the TEK provided
        data, the temperature profile should be given in Project"""
        demand = calc_bld_demand(self.building_typ, self.area, energy_sector)
        if energy_sector == 'heat':
            self.annual_demand["heat_demand"] = demand
        elif energy_sector == 'elec':
            self.annual_demand["elec_demand"] = demand
        else:
            warn("Other energy sector, except 'heat' and 'elec', are not "
                 "developed, so could not use the method. check again or fixe "
                 "the problem with changing this method add_annual_demand")

    def add_thermal_profile(self, energy_sector, temperature_profile):
        """The heat and cool demand profile could be calculated with
        temperature profile according to degree day method.
        Attention!!! The temperature profile could only provided in project
        object, so this method cannot be called in the initialization of
        building object."""
        # todo: the current version is only for heat, the method could be
        #  developed for cool demand later.
        if energy_sector == 'heat':
            heat_demand_profile = gen_heat_profile(self.building_typ,
                                                   self.area,
                                                   temperature_profile)
            self.demand_profile["heat_demand"] = heat_demand_profile
        elif energy_sector == 'cool':
            warn('Profile for cool is still not developed')
        else:
            warn_msg = 'The ' + energy_sector + ' is not allowed, check the ' \
                                                'method add_thermal_profile '

            warn(warn_msg)

    def add_elec_profile(self, year):
        """Generate the electricity profile with the 'Standardlastprofil'
        method. This method could only be called in the Project object,
        because the year is stored in the Environment object"""
        elec_demand_profile = gen_elec_profile(self.annual_demand[
                                                   "elec_demand"],
                                               self.building_typ,
                                               year)
        self.demand_profile["elec_demand"] = elec_demand_profile

    def add_topology(self, topology):
        topo_matrix = pd.read_csv(topology)
        self.topology = topo_matrix

    def add_components(self, env):
        """Generate the components according to topology matrix and add
        all the components to the self list"""
        if self.topology is None:
            warn('No topology matrix is found in building!')
        else:
            for item in self.topology.index:
                comp_name = self.topology['comp_name'][item]
                comp_type = self.topology['comp_type'][item]
                comp_model = self.topology['model'][item]
                if comp_type in ['HeatPump', 'GasHeatPump']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      temp_profile=
                                                      env.temp_profile,
                                                      comp_model=comp_model)
                elif comp_type in ['PV', 'SolarThermalCollector']:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      irr_profile=
                                                      env.irr_profile,
                                                      comp_model=comp_model)
                else:
                    comp_obj = module_dict[comp_type](comp_name=comp_name,
                                                      comp_model=comp_model)
                self.components[comp_name] = comp_obj

    def add_vars(self, model):
        """Add Pyomo variables into the ConcreteModel, which is defined in
        project object. So the model should be given in project object
        build_model.
        The following variable should be assigned:
            Energy flow from a component to another [t]: this should be define
            according to the component inputs and outputs possibility and the
            building topology. For each time step.
            Total Energy input and output of each component [t]: this should be
            assigned in each component object. For each time step.
            Component size: should be assigned in component object, for once.
        """
        # Assign the variables for the energy flows according to system
        # topology. The input energy type and output energy type could be
        # used to reduce the number of variables.
        # Simplify the matrix at first, only the topology related information
        # are left. Then search the items, which equal to 1, that means the
        # energy could flow from the index component to the column component.
        # The component pairs are stored in the dictionary energy_flow.
        simp_matrix = self.topology.drop(['comp_type', 'model', 'min_size',
                                          'max_size', 'current_size'], axis=1)
        simp_matrix.set_index(['comp_name'], inplace=True)
        energy_flow = {}
        for index, row in simp_matrix.iteritems():
            if len(row[row == 1].index.tolist()) > 1:
                for input_comp in row[row == 1].index.tolist():
                    energy_flow[(input_comp, index)] = pyo.Var(
                        model.time_step, bounds=(0, None))
                    model.add_component(input_comp + '_' + index,
                                        energy_flow[(input_comp, index)])
        # print(energy_flow)

        for comp in self.components:
            self.components[comp].add_vars(model)

    def add_cons(self, model):
        pass

    def _energy_balance(self, model):
        pass
