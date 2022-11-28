import warnings
import pyomo.environ as pyo
from pyomo.gdp import Disjunct, Disjunction

from scripts.FluidComponent import FluidComponent
from scripts.components.CHP import CHP

small_num = 0.0001


class CHPFluid(CHP, FluidComponent):

    def __init__(self, comp_name, comp_type="CHPFluid", comp_model=None,
                 min_size=50, max_size=400, current_size=0, sub_model="small"):
        """
        The model for CHP Fluid, which considers three sub model for
        different technical and economic parameter.

        small: the electricity power lower than 50 kW
        large: the electricity power lower than 400 kW. The small CHPs are
               classified in this category as well.
               In practice there are larger CHP than 400 kW, but it was not
               so often to be seen. If in a specific project, the sub models
               could be modified and generate new sub model for larger CHP.
        condensing: the CHP with condensing parts, which brings higher
               thermal efficiency for the component. The upper limit for
               condensing CHP is set to 50 kW electricity power.

        Compared with other components, the CHPFluid components could model
        the additional operation cost. For the start of CHP, the start cost
        is used to model the oil consumption by the start phase. The value
        for 5 euro comes from a technical website, an exact value could not
        be found.
        """
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size,
                         sub_model=sub_model)

        self.heat_flows_in = None
        self.heat_flows_out = []

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if 'outlet temperature' in properties.columns:
            self.outlet_temp = float(properties['outlet temperature'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for outlet temperature.")
            # Even the sub model with condensing part, the outlet temperature
            # could reach 80 grade. Because the inlet stream flows though the
            # low temperature condensing part at first, then flows though the
            # high temperature burning chamber. The temperature for sub model
            # small and large are set to 80, because of the purpose of
            # protecting motor from high temperature span.

            # These data could be found in the data sheet from the
            # manufacturer.
            # For small CHP the data sheet of YANMAR_BHKW-Broschuere was used.
            # (https://www.energysystem-yanmar.com/produktkataloge/YANMAR_BHKW-Broschuere.pdf)
            # For condensing CHP the data sheet of
            # EC_POWER_DE_Technisches_Datenblatt was used.
            # https://www.ecpower.eu/files/ec-power/customer/DE/Downloads_DE/EC_POWER_DE_Technisches_Datenblatt_XRGI9.pdf
            self.outlet_temp = 80

    def _constraint_therm_eff(self, model):
        """This method shows the relationship of thermal efficiency and the
        inlet temperature of a CHP. The relationship are derived from
        linearization method of Taylor expansion. The original method comes
        from the book (Solare Technologien für Gebäude: Grundlagen und
        Praxisbeispiele. Springer-Verlag, 2012)

        power_el: electricity power, which is defined as comp_size
        power_th: thermal nominal power

        The sub model contains the products smaller than 50 kW, so a GDP
        model is used here.

        The CHP could have variable inlet temperature, so the efficiency at
        each time step could vary as well. The
        """
        therm_size = model.find_component('therm_size_' + self.name)
        therm_eff = model.find_component('therm_eff_' + self.name)
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        if self.sub_model == "small":
            for t in model.time_step:
                model.cons.add(therm_eff[t] == - 0.0000355 * therm_size + 0.498)
        elif self.sub_model == "condensing":
            for t in model.time_step:
                model.cons.add(
                    therm_eff[t] == 0.759 - 0.0008 * (therm_size - 23.3) -
                    0.005 * (inlet_temp[t] - 30))
        elif self.sub_model == "large":
            if model.find_component('select_small_' + self.name):
                select_small = model.find_component('select_small_' + self.name)
            else:
                power_el = model.find_component('size_' + self.name)
                select_small = Disjunct()
                model.add_component('select_small_' + self.name, select_small)
                select_small_size = pyo.Constraint(expr=power_el <= 50)
                select_small.add_component('select_small_size_' + self.name,
                                           select_small_size)

            if model.find_component('select_large_' + self.name):
                select_large = model.find_component('select_large_' + self.name)
            else:
                power_el = model.find_component('size_' + self.name)
                select_large = Disjunct()
                model.add_component('select_large_' + self.name, select_large)
                select_large_size = pyo.Constraint(expr=power_el >= 50 +
                                                        small_num)
                select_large.add_component('select_large_size_' + self.name,
                                           select_large_size)

            small_cons_list = []
            for t in model.time_step:
                small_cons_list.append(pyo.Constraint(
                    expr=therm_eff[t] == - 0.0000355 * therm_size + 0.498))
                select_small.add_component(
                    'small_eff_con_'+self.name+'_'+str(t), small_cons_list[t])

            large_cons_list = []
            for t in model.time_step:
                large_cons_list.append(pyo.Constraint(
                    expr=therm_eff[t] == 0.496 - 0.0001 * (therm_size - 267) -
                         0.002 * (inlet_temp[t] - 47) - 0.0017 *
                         (self.outlet_temp - 67)))
                select_large.add_component(
                    'select_large_con_'+self.name+'_'+str(t),
                    large_cons_list[t])

            if not model.find_component('select_large_' + self.name):
                dj_power = Disjunction(expr=[select_small, select_large])
                model.add_component('disjunction_power_' + self.name, dj_power)

    def _constraint_temp(self, model):
        """verbinden die Parameter der einzelnen Anlage mit den Parametern
        zwischen zwei Anlagen (simp_matrix).
        todo check if we really need this method?"""
        inlet_temp = model.find_component('inlet_temp_' + self.name)
        for heat_output in self.heat_flows_out:
            t_in = model.find_component(
                heat_output[1] + '_' + heat_output[0] + '_' + 'temp')
            t_out = model.find_component(
                heat_output[0] + '_' + heat_output[1] + '_' + 'temp')
            for t in model.time_step:
                model.cons.add(self.outlet_temp == t_out[t])
                model.cons.add(inlet_temp[t] == t_in[t])
                # ZUr ausreichenden Abkühlung des Motors soll die Rücklauftemperatur des BHKW nicht
                # 70 Grad überschreiten.
                model.cons.add(inlet_temp[t] <= 70)

    def _constraint_mass_flow(self, model):
        for heat_output in self.heat_flows_out:
            m_in = model.find_component(heat_output[1] + '_' + heat_output[0] +
                                        '_' + 'mass')
            m_out = model.find_component(heat_output[0] + '_' + heat_output[1] +
                                         '_' + 'mass')
            for t in range(len(model.time_step) - 1):
                model.cons.add(m_in[t + 1] == m_out[t + 1])
                model.cons.add(m_in[t + 2] == m_in[t + 1])

    def add_cons(self, model):
        super().add_cons(model)
        self._constraint_therm_eff(model)
        self._constraint_temp(model)
        self._constraint_heat_outputs(model)

        # self._constraint_mass_flow(model)

    def add_vars(self, model):
        super().add_vars(model)

        therm_eff = pyo.Var(model.time_step, bounds=(0, 1))
        model.add_component('therm_eff_' + self.name, therm_eff)

        inlet_temp = pyo.Var(model.time_step, bounds=(12, 95))
        model.add_component('inlet_temp_' + self.name, inlet_temp)
