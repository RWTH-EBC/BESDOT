import pyomo.environ as pyo
# import pyomo
from pyomo.gdp import Disjunct, Disjunction

m = pyo.ConcreteModel('gdp_test')

######
# choose reactor
######
# m.F= pyo.Var(bounds=(0, 8), doc="Flow into reactor")
# m.X= pyo.Var(bounds=(0, 1), doc="Reactor conversion")
# m.d= pyo.Param(initialize=2, doc="Max product demand")
#
# m.c = pyo.Param([1, 2, 'I', 'II'], doc="Costs", initialize={
# 1: 2, # Value of product
# 2: 0.2, # Cost of raw material
# 'I': 2.5, # Cost of reactor I
# 'II': 1.5 # Cost of reactor II
# })
# m.alpha = pyo.Param(['I', 'II'], doc="Reactor coefficient", initialize={'I': -8, 'II': -10})
# m.beta = pyo.Param(['I', 'II'], doc="Reactor coefficient", initialize={'I': 9, 'II': 15})
# m.X_LB = pyo.Param(['I', 'II'], doc="Reactor conversion lower bound", initialize={'I': 0.2, 'II': 0.7})
# m.X_UB = pyo.Param(['I', 'II'], doc="Reactor conversion upper bound", initialize={'I': 0.95, 'II': 0.99})
# m.C_rxn = pyo.Var(bounds=(1.5, 2.5), doc="Cost of reactor")
# m.max_demand = pyo.Constraint(expr=m.F * m.X <= m.d, doc="product demand")
# m.reactor_choice = Disjunction(expr=[[m.F == m.alpha['I'] * m.X + m.beta['I'],m.X_LB['I'] <= m.X,m.X <= m.X_UB['I'],m.C_rxn == m.c['I']],
# # Disjunct 2: Choose reactor II
# [m.F == m.alpha['II'] * m.X + m.beta['II'],m.X_LB['II'] <= m.X,m.X <= m.X_UB['II'],m.C_rxn == m.c['II']]
# ], xor=True)
# m.profit = pyo.Objective(expr=m.c[1] * m.F * m.X - m.c[2] * m.F - m.C_rxn, sense=pyo.maximize)


######
# Disjunct example from tutorial
######
# m.n = pyo.RangeSet(4)
# m.x = pyo.Var(m.n)
# m.unit1 = Disjunct()
# m.unit1.inout = pyo.Constraint(expr=pyo.exp(m.x[2]) - 1 == m.x[1])
# m.unit1.no_unit2_flow1 = pyo.Constraint(expr=m.x[3] == 0)
# m.unit1.no_unit2_flow2 = pyo.Constraint(expr=m.x[4] == 0)
# m.unit2 = Disjunct()
# m.unit2.inout = pyo.Constraint(expr=pyo.exp(m.x[4] / 1.2) - 1 == m.x[3])
# m.unit2.no_unit1_flow1 = pyo.Constraint(expr=m.x[1] == 0)
# m.unit2.no_unit1_flow2 = pyo.Constraint(expr=m.x[2] == 0)
# m.use_unit1or2 = Disjunction(expr=[m.unit1, m.unit2])

# m.I = pyo.RangeSet(5)
# m.Y = pyo.BooleanVar(m.I)
#
# @m.LogicalConstraint(m.I)
# def p(m,i):
#     return m.Y[i+1].implies(m.Y[i]) if i < 5 else pyo.Constraint.Skip
#
# m.p.pprint()

# m.x = pyo.Var(bounds=(0,10))
# m.y = pyo.Var(within=pyo.Binary)
#
# m.unit1 = Disjunct()
# m.unit1.cons_1 = pyo.ConstraintList()
# m.unit1.cons_1.add(m.x >= 0)
# m.unit1.cons_1.add(m.x <= 5)
# m.unit1.cons_1.add(m.y == 0)
#
# m.unit2 = Disjunct()
# m.unit2.cons_2 = pyo.ConstraintList()
# m.unit2.cons_2.add(m.x >= 5)
# m.unit2.cons_2.add(m.x <= 10)
# m.unit2.cons_2.add(m.y == 1)
#
# m.use_unit1or2 = Disjunction(expr=[m.unit1, m.unit2])
#
# m.select = pyo.Constraint(expr=m.x == 7)
#
# m.o = pyo.Objective(expr=m.y+m.x)
# pyo.TransformationFactory('gdp.bigm').apply_to(m)
# run_data = pyo.SolverFactory('glpk').solve(m)
# pyo.Reference(m.unit2[:].indicator_var).display()
# pyo.Reference(m.unit1[:].indicator_var).display()

# m.s = pyo.RangeSet(4)
# m.ds = pyo.RangeSet(2)
# m.d = Disjunct(m.s)
# m.djn = Disjunction(m.ds)
# m.djn[1] = [m.d[1], m.d[2]]
# m.djn[2] = [m.d[3], m.d[4]]
# m.x = pyo.Var(bounds=(-2, 10))
# m.d[1].indicator = pyo.BooleanVar()
# m.d[1].c = pyo.Constraint(expr=m.x >= 2)
# m.d[2].indicator = pyo.BooleanVar()
# m.d[2].c = pyo.Constraint(expr=m.x >= 3)
# m.d[3].indicator = pyo.BooleanVar()
# m.d[3].c = pyo.Constraint(expr=m.x <= 8)
# m.d[4].indicator = pyo.BooleanVar()
# m.d[4].c = pyo.Constraint(expr=m.x == 2.5)
# m.o = pyo.Objective(expr=m.x)
#
# print(type(m.d[1].indicator_var))
# print(m.d[1].indicator_var)
# print(type(m.d[1].c))
# print(m.d[1].c)
# m.pprint()
#
# m.p = pyo.LogicalConstraint(expr=m.d[1].indicator.implies(m.d[4].indicator))
pyo.TransformationFactory('gdp.chull').apply_to(m)
# pyo.Reference(m.d[:].indicator_var).display()
run_data = pyo.SolverFactory('BONMIN').solve(m, tee=True)
# pyo.Reference(m.d[:].indicator_var).display()
# m.pprint()
for v in m.component_objects(pyo.Var, active=True):
    print("Variable component object",v)
    for index in v:
        print("   ", v[index], v[index].value)
