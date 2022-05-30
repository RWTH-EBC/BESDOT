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

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_loss(model, loss_type='off')
        self._constraint_temp(model, init_temp=30)
        self._constraint_heat_outputs(model)
        self._constraint_vdi2067(model)
        if self.cluster is not None:
            self._constraint_conserve(model)
        else:
            self._constriant_unchange(model)

    def add_vars(self, model):
        super().add_vars(model)





