import pyomo.environ as pyo
# import pyomo
from pyomo.gdp import Disjunct, Disjunction

small_num = 0.00001
m = pyo.ConcreteModel('gdp_test')

######
# choose reactor use case
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
#
# m.I = pyo.RangeSet(5)
# m.Y = pyo.BooleanVar(m.I)
#
# @m.LogicalConstraint(m.I)
# def p(m,i):
#     return m.Y[i+1].implies(m.Y[i]) if i < 5 else pyo.Constraint.Skip
#
# m.p.pprint()

######
# LogicalConstraint
######
# m.p = pyo.LogicalConstraint(expr=m.d[1].indicator.implies(m.d[4].indicator))

######
# test BooleanVar
######
# m.a = pyo.BooleanVar()
# m.c = pyo.Constraint(expr=m.a==True)

######
# test multiple Disjunction
######
# m.t = pyo.Var(bounds=(20,70))
# m.energy = pyo.Var(bounds=(30,50))
# m.choice_1 = Disjunction(expr=[[m.t >= 60, m.energy == 0], []])
# m.choice_2 = Disjunction(expr=[[m.t <= 30], [m.energy == 0]])
# # m.choice_3 = Disjunction(expr=[m.choice_1, m.choice_2])
# m.profit = pyo.Objective(expr=3*m.energy + m.t)
#
# pyo.SolverFactory('gurobi').solve(m, tee=True)
# for v in m.component_objects(pyo.Var, active=True):
#     print("Variable component object",v)
#     for index in v:
#         print("   ", v[index], v[index].value)

######
# gdp transformation and solve model
######

# pyo.TransformationFactory('gdp.bigm').apply_to(m)
# run_data = pyo.SolverFactory('glpk').solve(m, tee=True)
# for v in m.component_objects(pyo.Var, active=True):
#     print("Variable component object",v)
#     for index in v:
#         print("   ", v[index], v[index].value)

######
# another example from documentation
######
# m.s = pyo.RangeSet(4)
# m.ds = pyo.RangeSet(2)
# m.d = Disjunct(m.s)
# m.djn = Disjunction(m.ds)
# m.djn[1] = [m.d[1], m.d[2]]
# m.djn[2] = [m.d[3], m.d[4]]
# m.x = pyo.Var(bounds=(-2, 10))
# m.d[1].c = pyo.Constraint(expr=m.x >= 2)
# m.d[2].c = pyo.Constraint(expr=m.x >= 3)
# m.d[3].c = pyo.Constraint(expr=m.x <= 8)
# m.d[4].c = pyo.Constraint(expr=m.x == 2.5)
# m.o = pyo.Objective(expr=m.x)
#
# # Add the logical proposition
# m.p = pyo.LogicalConstraint(
#    expr=m.d[1].indicator_var.implies(m.d[4].indicator_var))
# # Note: the implicit XOR enforced by m.djn[1] and m.djn[2] still apply
#
# # Apply the Big-M reformulation: It will convert the logical
# # propositions to algebraic expressions.
# pyo.TransformationFactory('gdp.hull').apply_to(m)
#
# # Before solve, Boolean vars have no value
# pyo.Reference(m.d[:].indicator_var).display()
#
# # Solve the reformulated model
# run_data = pyo.SolverFactory('glpk').solve(m)
# pyo.Reference(m.d[:].indicator_var).display()

#######
# a test
#######
time_steps = 24

m.t = pyo.RangeSet(time_steps)
m.temp = pyo.Var(m.t, bounds=(20,70))
m.energy = pyo.Var(m.t, bounds=(0,15))

m.init = pyo.BooleanVar()
m.p_init = pyo.LogicalConstraint(expr=m.init.equivalent_to(True))

m.o = pyo.Objective(expr=pyo.quicksum(m.energy[time] for time in m.t))
m.temp_con = pyo.Constraint(expr=m.temp[1]==20)
m.temp_con_2 = pyo.Constraint(expr=m.temp[2]==25)

for time_step in m.t:
    a = Disjunct()
    c_1 = pyo.Constraint(expr=m.temp[time_step]>=60)
    c_2 = pyo.Constraint(expr=m.energy[time_step]==0)
    m.add_component('a_dis_'+str(time_step), a)
    a.add_component('a_1_'+str(time_step), c_1)
    a.add_component('a_2_' + str(time_step), c_2)

    b = Disjunct()
    c_7 = pyo.Constraint(expr=m.temp[time_step] <= 60-small_num)
    c_8 = pyo.Constraint(expr=m.energy[time_step] >= 10)
    m.add_component('b_dis_'+str(time_step), b)
    b.add_component('b_1_' + str(time_step), c_7)
    b.add_component('b_2_' + str(time_step), c_8)

    c = Disjunct()
    c_3 = pyo.Constraint(expr=m.temp[time_step]<=30)
    c_5 = pyo.Constraint(expr=m.energy[time_step]>=6)
    m.add_component('c_dis_'+str(time_step), c)
    c.add_component('c_' + str(time_step), c_3)
    c.add_component('c_2_' + str(time_step), c_5)

    d = Disjunct()
    c_4 = pyo.Constraint(expr=m.energy[time_step]==0)
    c_6 = pyo.Constraint(expr=m.temp[time_step] >= 30+small_num)
    m.add_component('d_dis_'+str(time_step), d)
    d.add_component('d_' + str(time_step), c_4)
    d.add_component('d_2_' + str(time_step), c_6)

    dj = Disjunction(pyo.RangeSet(2))
    m.add_component('dj_dis_' + str(time_step), dj)
    # dj[1] = [a, b]
    # dj[2] = [c, d]
    dj[1] = [a, b, c, d]
    if time_step == 1:
        # p_3 = pyo.LogicalConstraint(expr=pyo.xor(m.init, b.indicator_var))
        # p_4 = pyo.LogicalConstraint(expr=pyo.lor(a.indicator_var, b.indicator_var).implies(m.init))
        p_4 = pyo.LogicalConstraint(
            expr=m.init.equivalent_to(pyo.lor(a.indicator_var, b.indicator_var)))
        p_5 = pyo.LogicalConstraint(
            expr=~m.init.equivalent_to(pyo.lor(c.indicator_var, d.indicator_var)))
    else:
        last_status = m.find_component('b_dis_'+str(time_step-1))
        # p_3 = pyo.LogicalConstraint(expr=pyo.xor(last_status.indicator_var, b.indicator_var))
        p_4 = pyo.LogicalConstraint(
            expr=pyo.lor(a.indicator_var, b.indicator_var).equivalent_to(last_status.indicator_var))
        # p_4 = pyo.LogicalConstraint(
        #     expr=last_status.indicator_var.implies(pyo.lor(a.indicator_var, b.indicator_var)))
        p_5 = pyo.LogicalConstraint(
            expr=~last_status.indicator_var.equivalent_to(pyo.lor(c.indicator_var, d.indicator_var)))
    # m.add_component('p_3_' + str(time_step), p_3)
    m.add_component('p_4_' + str(time_step), p_4)
    m.add_component('p_5_' + str(time_step), p_5)

pyo.TransformationFactory('gdp.bigm').apply_to(m)

# Before solve, Boolean vars have no value
# pyo.Reference(m.d[:].indicator_var).display()

# Solve the reformulated model
run_data = pyo.SolverFactory('glpk').solve(m)
print('##########')
# pyo.Reference(m.d[:].indicator_var).display()
print('##########')
for v in m.component_objects(pyo.Var, active=True):
    # print("Variable component object",v)
    for index in v:
        print("   ", v[index], v[index].value)