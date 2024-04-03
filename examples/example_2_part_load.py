"""
This example optimize the energy system with the consideration of
hydraulic constrains for heat supply.
"""

import os
from scripts.Project import Project
from scripts.Environment import Environment
from scripts.Building import Building
from scripts.components.ElectricBoiler import ElectricBoiler
import utils.post_processing as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

################################################################################
#                           Generate python objects
################################################################################

# Generate a project object at first.
project = Project(name='project_2', typ='building')

# Generate the environment object
env_2 = Environment(time_step=3)
project.add_environment(env_2)

# If the objective of the project is the optimization for building, a building
# should be added to the project.
bld_2 = Building(name='bld_2', area=200)


# Add the energy demand profiles to the building object
# Attention! generate thermal with profile whole year temperature profile
# bld_2.add_thermal_profile('heat', env_2.temp_profile_original, env_2)



# Pre define the building energy system with the topology for different
# components and add components to the building.


################################################################################
#                        Build pyomo model and run optimization
################################################################################


################################################################################
#                                  Post-processing
################################################################################

