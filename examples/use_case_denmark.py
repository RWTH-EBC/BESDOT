"""
Use case for a Denmark district. This use case should be applied for an
energy hub, which could be seen as a building. So the project typ is taken
with 'building'
"""

import os
import pandas as pd
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='denmark_energy_hub', typ='building')

# Generate the environment object, which contains the weather data and price
# data.
# Attention! The weather file from partner is not the formate of DWD,
# so we should change the environment to add the weather information.
# todo: if this case is common, should change the Enviroment class.
env_denmark = Environment()
env_denmark.elec_price = 0.26  # €/kWh
# todo: the electricity price for heat pump is cheaper with 0.21 €/kWh
env_denmark.elec_feed_price = 0.09
env_denmark.gas_price = 0.043
env_denmark.co2_price = 31.6
env_denmark.elec_emission = 410
env_denmark.gas_emission = 200

weather_file = os.path.join(base_path, 'data', 'denmark_energy_hub',
                            'weather.csv')
weather_df = pd.read_csv(weather_file, header=0, skiprows=1)
weather_df = weather_df.drop(index=[0])
temperature_profile = weather_df['temp_dry'].astype('float64').values
wind_profile = weather_df['wind_speed'].astype('float64').values
total_solar_profile = weather_df['radia_glob'].astype('float64').values

env_denmark.temp_profile = temperature_profile
env_denmark.wind_profile = wind_profile
env_denmark.irr_profile = total_solar_profile

project.add_environment(env_denmark)

# The building class is not rationally designed, so need to change the demand
# profile
# todo: add demand profile instead of area and annual demand
energy_hub = Building(name='energy_hub', area=200, solar_area=1000000)

demand_file = os.path.join(base_path, 'data', 'denmark_energy_hub',
                           'energyprofile(kwh).csv')
demand_df = pd.read_csv(demand_file)
commercial_heat = demand_df['commercial heat'].astype('float64').values
resident_heat = demand_df['residential heat'].astype('float64').values
total_heat = commercial_heat + resident_heat
total_elec = demand_df['total electricity'].astype('float64').values
print(max(total_elec))
print(max(total_heat))

energy_hub.demand_profile['elec_demand'] = total_elec
energy_hub.demand_profile['heat_demand'] = total_heat

# Pre define the building energy system with the topology for different
# components and add components to the building.
topo_file = os.path.join(base_path, 'data', 'topology', 'simp_district.csv')
energy_hub.add_topology(topo_file)
energy_hub.add_components(project.environment)
project.add_building(energy_hub)

################################################################################
#                        Build pyomo model and run optimization
################################################################################
project.build_model()
project.run_optimization('gurobi')

################################################################################
#                                  Post-processing
################################################################################

