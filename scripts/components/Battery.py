from scripts.components.Storage import Storage
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction

class Battery(Storage):

    def __init__(self, comp_name, comp_type="Battery", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        self.inputs = ['elec']
        self.outputs = ['elec']

        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_init_energy(self, model):
        stored_energy = model.find_component('energy_' + self.name)
        model.cons.add(stored_energy[1] == 0)

    def _constraint_conver_loss(self, model):
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        stored_energy = model.find_component('energy_' + self.name)

        for t in range(1, len(model.time_step)):
            t = Disjunct()
            c_1 = pyo.Constraint(expr=input_energy[t] -
                           output_energy[t] == stored_energy[t+1] - stored_energy[t])
            c_2 = pyo.Constraint(expr=stored_energy[t] == 0)
            model.add_component('t_dis_' + str(t), t)
            t.add_component('t_1' + str(t), c_1)
            t.add_component('t_2' + str(t), c_2)

            r = Disjunct()
            c_3 = pyo.Constraint(expr=input_energy[t] -
                                      output_energy[t] - 0.00001 == stored_energy[t + 1] - stored_energy[t])
            model.add_component('r_dis_' + str(t), r)
            r.add_component('r_1' + str(t), c_3)

            dj8 = Disjunction(expr=[t, r])
            model.add_component('dj8_dis_' + str(t), dj8)

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_maxpower(model)
        self._constraint_maxcap(model)
        self._constraint_vdi2067(model)
        self._constraint_init_energy(model)
        self._constraint_conserve(model)