import warnings
from scripts.components.HomoStorage import HomoStorage


class HomoStorageST(HomoStorage):
    def __init__(self, comp_name, comp_type="HomoStorageST", comp_model=None,
                 min_size=0, max_size=1000, current_size=0):
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)

    def _constraint_temp(self, model, init_temp=30):
        super()._constraint_temp(model=model, init_temp=init_temp)

        temp_var = model.find_component('temp_' + self.name)
        for t in model.time_step:
            model.cons.add(temp_var[t] >= self.min_temp)
            model.cons.add(temp_var[t] <= self.max_temp)

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_loss(model, loss_type='off')
        self._constraint_temp(model)
        self._constraint_heat_outputs(model)
        self._constraint_vdi2067(model)

    def add_vars(self, model):
        super().add_vars(model)





