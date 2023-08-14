import warnings
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy


small_nr = 0.00001


class EEG(Subsidy):
    """
    EEG means 'Erneuerbare Energie Gesetz' (Renewable Energy Sources Act),
    which provide a feed-in tariff to encourage the generation of renewable
    electricity. In this tool 'besdot' the subsidy for PV is considered,
    since other energy source are barely found in building.

    The subsidy for PV could be sorted into 3 types: 'Direktvermarktung',
    'Einspeiseverguetung' and 'Mieterstromzuschlag'. For these three sudsidy
    possibility, the profit for building holder is almost same, only the
    settlement is a little different. According to the latest EEG in 2021,
    only the device smaller than 500 kW in building could be supplied with
    subsidies. (The upper limit for free land PV is 750 kW! The upper limit
    for 'Mieterstromzuschlag' is 100 kW, The limit for 'Einspeiseverguetung'
    is 100 kW as well.) The subsidies amount for PVs are determined with a
    tendering process. So these value need to be updated after each tendering
    process.

    The latest data comes from 30. Juli 2022:
    Size < 10 kWp: 8.6 cent/kWh
    10kWh <= Size < 40 kWp: 7.5 cent/kWh
    40kWh <= Size < 500 kWp: 6.2 cent/kWh
    500kWh <= Size: 0 cent/kWh

    The subsidy amount will be reduced by 0.5% for each month, until to the
    new tendering process.
    todo: The calculation for subsidy depression should be done later.
    """

    def __init__(self):
        super().__init__(enact_year=2021)
        self.name = 'EEG'
        self.components = ['PV']
        self.type = 'operate'
        self.energy_pair = []

    def analyze_topo(self, building):
        # analyze the topology of the building and add the relevant device
        # and energy flow or even hydraulic flow pairs into the subsidy object.
        pv_name = None
        grid_name = None
        for index, item in building.topology.iterrows():
            if item["comp_type"] == "PV":
                pv_name = item["comp_name"]
            elif item["comp_type"] == "ElectricityGrid":
                grid_name = item["comp_name"]
        if pv_name is not None and grid_name is not None:
            self.energy_pair.append([pv_name, grid_name])
        else:
            warnings.warn("Not found PV name or electricity grid name.")

    def add_cons(self, model):
        # Find the corresponding model variables at first. The subsidy is only
        # for feed-in tariff. So the relevant variable is the electricity from
        # PV to electricity grid. If in the building contain other
        # electricity generation device like CHP, the electricity need to be
        # seperated. If a battery is also added, the electricity from battery
        # is hard to identify. So in this version, the subsidy only consider
        # the electricity from PV to electricity.
        pv_grid_flow = model.find_component('elec_' + self.energy_pair[
            0][0] + '_' + self.energy_pair[0][1])
        pv_grid_total = model.find_component('subsidy_' + self.name +
                                             '_PV_energy')
        pv_size = model.find_component('size_' + self.energy_pair[0][0])
        subsidy = model.find_component('subsidy_' + self.name + '_PV')

        # Sum up all the energy flows at each time step.
        # model.cons.add(pv_grid_total == sum(pv_grid_flow[t]) for t in
        #                model.time_step)
        model.cons.add(pv_grid_total == sum(pv_grid_flow[t] for t in
                       model.time_step))

        # GDP model for different tariff according to the PV size, the tariff
        # is hard coded, because the tariff model could change.
        tariff_1 = Disjunct()
        tariff_1_size = pyo.Constraint(expr=pv_size <= 10 + small_nr)
        tariff_1_subsidy = pyo.Constraint(expr=subsidy == pv_grid_total * 0.086)
        model.add_component(self.name + 'tariff_1', tariff_1)
        tariff_1.add_component(self.name + 'tariff_1_size', tariff_1_size)
        tariff_1.add_component(self.name + 'tariff_1_subsidy', tariff_1_subsidy)

        tariff_2 = Disjunct()
        tariff_2_size_1 = pyo.Constraint(expr=pv_size <= 40 + small_nr)
        tariff_2_size_2 = pyo.Constraint(expr=pv_size >= 10)
        tariff_2_subsidy = pyo.Constraint(expr=subsidy == pv_grid_total * 0.075)
        model.add_component(self.name + 'tariff_2', tariff_2)
        tariff_2.add_component(self.name + 'tariff_2_size_1', tariff_2_size_1)
        tariff_2.add_component(self.name + 'tariff_2_size_2', tariff_2_size_2)
        tariff_2.add_component(self.name + 'tariff_2_subsidy', tariff_2_subsidy)

        tariff_3 = Disjunct()
        tariff_3_size_1 = pyo.Constraint(expr=pv_size <= 500 + small_nr)
        tariff_3_size_2 = pyo.Constraint(expr=pv_size >= 40)
        tariff_3_subsidy = pyo.Constraint(expr=subsidy == pv_grid_total * 0.062)
        model.add_component(self.name + 'tariff_3', tariff_3)
        tariff_3.add_component(self.name + 'tariff_3_size_1', tariff_3_size_1)
        tariff_3.add_component(self.name + 'tariff_3_size_2', tariff_3_size_2)
        tariff_3.add_component(self.name + 'tariff_3_subsidy', tariff_3_subsidy)

        tariff_4 = Disjunct()
        tariff_4_size = pyo.Constraint(expr=pv_size >= 500)
        tariff_4_subsidy = pyo.Constraint(expr=subsidy == 0)
        model.add_component(self.name + 'tariff_4', tariff_4)
        tariff_4.add_component(self.name + 'tariff_4_size', tariff_4_size)
        tariff_4.add_component(self.name + 'tariff_4_subsidy', tariff_4_subsidy)

        dj_subsidy = Disjunction(expr=[tariff_1, tariff_2, tariff_3, tariff_4])
        model.add_component('disjunction_subsidy' + self.name, dj_subsidy)

    def add_vars(self, model):
        super().add_vars(model)

        total_energy = pyo.Var(bounds=(0, 10 ** 10))
        model.add_component('subsidy_' + self.name + '_PV_energy',
                            total_energy)
