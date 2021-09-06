"""
This script is an example for the class project, which shows the process for
building an optimization model.
"""

from scripts.Project import Project
from scripts.Building import Building

# Generate a project at first.
test_project = Project(name='project_1', typ='building')

# If the objective of the project is the optimization for building, a building
# should be added to the project.
test_bld_1 = Building(name='bld_1')

# todo: add building profiles
test_bld_1.add_profile()

# todo: pre define the building energy system. The topology for different
#  components

test_project.add_building(test_bld_1)

#

