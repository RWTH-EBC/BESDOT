import os
import warnings
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction
from scripts.Subsidy import Subsidy
import pandas as pd

small_nr = 0.00001

script_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_folder, '../..', 'data', 'subsidy', 'country_subsidy_EEG.csv')
subsidy_data = pd.read_csv(csv_file_path)


# Definition of the EEG class, which inherits from the Subsidy class. In the constructor method __init__,
# some attributes are initialized, including name, components, type, etc. The constructor also calls the
# constructor of the parent class Subsidy and sets feed_type and tariff_rate.
class EEG(Subsidy):
    def __init__(self, feed_type, tariff_rate):
        super().__init__(enact_year=2023)
        self.name = 'EEG'
        self.components = ['PV']
        self.type = 'operate'
        self.energy_pair = []
        self.subsidy_data = subsidy_data
        self.feed_type = feed_type
        self.tariff_rate = tariff_rate

    # This method is used to analyze the building's topology information to determine the connection between PV and
    # the grid. It iterates through the topology information of the building object and adds them to the energy_pair
    # attribute if a connection is found. If no connection is found, a warning is issued.
    def analyze_topo(self, building):
        pv_name = None
        e_grid_name = None
        for index, item in building.topology.iterrows():
            if item["comp_type"] == "PV":
                pv_name = item["comp_name"]
            elif item["comp_type"] == "ElectricityGrid":
                e_grid_name = item["comp_name"]
        if pv_name is not None and e_grid_name is not None:
            self.energy_pair.append([pv_name, e_grid_name])
        else:
            warnings.warn("Not found PV name or electricity grid name.")

    # This method is used to add constraints to the model. First, it finds PV and grid-related model components based
    # on energy_pair and the model's component names. Then it adds a constraint to ensure that the total grid flow
    # equals the sum of grid flow at each time step. Next, it iterates through each row of subsidy data, checking if
    # the "Feed Type" matches the customer's selected feed_type. If it matches, it selects the appropriate subsidy rate
    # based on the customer's selected tariff_rate and creates constraints and inequalities accordingly.
    def add_cons(self, model):
        pv_grid_flow = model.find_component('elec_' + self.energy_pair[
            0][0] + '_' + self.energy_pair[0][1])
        pv_grid_total = model.find_component('subsidy_' + self.name +
                                             '_PV_energy')
        pv_size = model.find_component('size_' + self.energy_pair[0][0])
        subsidy = model.find_component('subsidy_' + self.name + '_PV')

        model.cons.add(pv_grid_total == sum(pv_grid_flow[t] for t in model.time_step))

        for idx, row in self.subsidy_data.iterrows():
            if row['Feed Type'] == self.feed_type:
                lower_bound = row['Size Lower']
                upper_bound = row['Size Upper']

                # Select the correct tariff rate based on the customer's choice
                if self.tariff_rate == 'Direkte Vermarktung':
                    subsidy_rate = row['Direkte Vermarktung']
                elif self.tariff_rate == 'Feste Verguetung':
                    subsidy_rate = row['Feste Verguetung']
                else:
                    raise ValueError("Invalid tariff rate selected")

                tariff = Disjunct()

                size_constraint = None
                size_constraint_lower = None
                size_constraint_upper = None

                if upper_bound == float('inf'):
                    size_constraint = pyo.Constraint(expr=pv_size >= lower_bound)
                else:
                    size_constraint_lower = pyo.Constraint(expr=pv_size >= lower_bound)
                    size_constraint_upper = pyo.Constraint(expr=pv_size <= upper_bound + small_nr)

                subsidy_constraint = pyo.Constraint(expr=subsidy == pv_grid_total * subsidy_rate)

                tariff_name = self.name + '_tariff_' + str(idx)
                model.add_component(tariff_name, tariff)

                if upper_bound == float('inf'):
                    tariff.add_component(tariff_name + '_size_constraint', size_constraint)
                else:
                    tariff.add_component(tariff_name + '_size_constraint_lower', size_constraint_lower)
                    tariff.add_component(tariff_name + '_size_constraint_upper', size_constraint_upper)

                tariff.add_component(tariff_name + '_subsidy_constraint', subsidy_constraint)

        tariff_disjunction_expr = [model.find_component(f'{self.name}_tariff_{idx}') for idx, row
                                   in self.subsidy_data.iterrows() if row['Feed Type'] == self.feed_type]
        dj_subsidy = Disjunction(expr=tariff_disjunction_expr)
        model.add_component(f'disjunction_subsidy_{self.name}', dj_subsidy)

    # This method is used to add variables to the model. It first calls the add_vars method of the parent
    # class Subsidy. Then it creates a variable named 'subsidy_' + self.name + '_PV_energy' to represent
    # the subsidy for PV energy.
    def add_vars(self, model):
        super().add_vars(model)

        total_energy = pyo.Var(bounds=(0, 10 ** 10))
        model.add_component(f'subsidy_{self.name}_PV_energy', total_energy)
