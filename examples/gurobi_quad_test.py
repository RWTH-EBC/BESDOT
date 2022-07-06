import pyomo.environ as pyo

m = pyo.ConcreteModel('quad_test')

m.a = pyo.Var(bounds=(20, 70))
m.b = pyo.Var(bounds=(5, 15))
m.c = pyo.Var(bounds=(10, 1000))
m.d = pyo.Var(bounds=(0, None))
m.e = pyo.Var(bounds=(0, None))

m.o = pyo.Objective(expr=m.e)
m.con_test_1 = pyo.Constraint(expr=2 * m.b >= m.a)
m.con_test_2 = pyo.Constraint(expr=m.a * m.b == m.c)
m.con_test_3 = pyo.Constraint(expr=m.c * m.d == m.e)
m.con_test_4 = pyo.Constraint(expr=2 * m.a <= m.d)
# m.con_test_5 = pyo.Constraint(expr=m.a == 25)
# m.con_test_6 = pyo.Constraint(expr=m.d == 60)

# Solve the reformulated model
solver = pyo.SolverFactory('gurobi')
solver.options['NonConvex'] = 2
solver.solve(m, tee=True)
print('##########')
# pyo.Reference(m.d[:].indicator_var).display()
print('##########')
for v in m.component_objects(pyo.Var, active=True):
    # print("Variable component object",v)
    for index in v:
        print("   ", v[index], v[index].value)
