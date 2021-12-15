import pyomo.environ as pyo

model = pyo.ConcreteModel('test')

# temp = pyo.Var()
# model.add_component(('temp', 'a'), temp)
energy_flow = {}
energy_flow[('a', 'b')] = pyo.Var()
model.add_component('a' + '_' + 'b', energy_flow[('a', 'b')])

energy_flow[('a', 'c')] = pyo.Var()
model.add_component('a' + '_' + 'c', energy_flow[('a', 'c')])

# print(model.temp['a', 'a'])
# print(model.find_component('a' + '_' + 'd'))
if not model.find_component('a' + '_' + 'c'):
    print('find it')
else:
    print('find that')

# name = 'a' + '_' + 'b'
# if not model.find_component('a_c'):
#     print('find it')
