from scripts.Component import Component
import warnings
import pyomo.environ as pyo
from scripts.FluidComponent import FluidComponent
from scripts.components.HeatExchangerFluid import HeatExchangerFluid
from scripts.pmv import *
import math

# Common parameters
water_heat_cap = 4.18 * 10 ** 3  # Unit J/kgK
water_density = 1000  # kg/m3
unit_switch = 3600 * 1000  # J/kWh

# todo (xzh&yni): hard codes need to modified
base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
output_path = os.path.join(base_path, "data", "weather_data",
                           "Dusseldorf", "pmv_coeff.csv")
data = pd.read_csv(output_path)
pmv = data.loc[:, 'coeff']
b = pmv.values.tolist()


class UnderfloorHeat(HeatExchangerFluid):
    def __init__(self, comp_name, temp_profile, comp_type="UnderfloorHeat",
                 comp_model=None, min_size=0, max_size=5000000,
                 current_size=0, comfort_model=False):
        """
        This class is used to generate the floor heating model and can be
        considered whether to add a user comfort model.
        Args:
            comp_name: same as Component
            temp_profile: temperature profile for each hour, necessary when
            calculating the comfort level.
            comp_type: same as Component
            comp_model: same as Component
            min_size: same as Component
            max_size: same as Component
            current_size: same as Component
            comfort_model: decide whether to consider user comfort models,
            i.e. pmv models. Default with False, which means not considered.
        """
        super().__init__(comp_name=comp_name,
                         comp_type=comp_type,
                         comp_model=comp_model,
                         min_size=min_size,
                         max_size=max_size,
                         current_size=current_size)
        # The outlet energy flow of floor heat is seen as pure energy flow.
        # would not be seen as as water flow. so heat_flows_out need to be
        # set as None, otherwise as child class of FluidComponent, it would
        # generate the mass flow and temperature variable for the outlet.
        self.heat_flows_out = None
        self.temp_profile = temp_profile
        self.comfort_model = comfort_model

        # The floor heating will only be turned on when the outdoor
        # temperature drops below this temperature. The hard coded value 15
        # grad comes from recommended value for germany building, this is
        # also used in tools/generate_heat_profile.
        self.start_temp = 15

        self.constant_inlet_temp = True

    def _read_properties(self, properties):
        super()._read_properties(properties)
        if 'inlet_temp' in properties.columns:
            self.inlet_temp = float(properties['inlet_temp'])
        else:
            warnings.warn("In the model database for " + self.component_type +
                          " lack of column for inlet temperature.")
            self.inlet_temp = 40

    def _constraint_conver(self, model):
        input_energy = model.find_component('input_' + self.inputs[0] + '_' +
                                            self.name)
        output_energy = model.find_component('output_' + self.outputs[0] + '_' +
                                             self.name)

        for t in model.time_step:
            model.cons.add(input_energy[t] == output_energy[t])

    def _constraint_temp(self, model):
        temp_var = model.find_component('temp_' + self.name)
        if self.constant_inlet_temp:
            for t in model.time_step:
                if self.temp_profile[t - 1] >= self.start_temp:
                    pass
                    # model.cons.add(temp_var[t] == 0)
                else:
                    model.cons.add(temp_var[t] == self.inlet_temp)
                    # model.cons.add(return_temp_var[t] + 2 <= temp_var[t])
        else:
            warnings.warn('Add temperature limit for UnderfloorHeat!')
            # todo (yni): the following scripts means the water flow from
            #  other component should be same as the input temperature of
            #  UnderFloorHeat. These constraints are supposed to be added in
            #  FluidComponent or in Building. Check it later.
            # for heat_input in self.heat_flows_in:
            #     t_out = model.find_component(heat_input[0] + '_' +
            #                                  heat_input[1] + '_' + 'temp')
            #     for t in range(len(model.time_step)):
            #         model.cons.add(temp_var[t + 1] == t_out[t + 1])

    # def _constraint_return_temp(self, model):
    #     return_temp_var = model.find_component('return_temp_' + self.name)
    #     for heat_input in self.heat_flows_in:
    #         t_in = model.find_component(heat_input[1] + '_' + heat_input[0] +
    #                                     '_' + 'temp')
    #         for t in range(len(model.time_step)):
    #             model.cons.add(return_temp_var[t + 1] == t_in[t + 1])

    # The total heat output of the underfloor heating can be calculated by the
    # above equation.
    # A: The area-specific heat output can be calculated on the room area.
    # q=8.92*(T_floor - T_air)^1.1 W/m2 can be approximated as a linearization
    # according to the Taylor expansion formula
    # Q=q*A, q:heat flux
    # Relation between surface temperature and average water temperature :
    # Tboden = 0.625(Taverage water temp) + 6.875 reference:A new simplified
    # model to calculate surface temperature and heat transfer of radiant floor
    # heating and cooling systems, Xiaozhou Wu, Jianing Zhao, Bjarne W. Olesen,
    # Lei Fang, Fenghao Wang
    def _constraint_floor_temp(self, model, floor_temp_approximate=24,
                               room_temp_approximate=21):
        input_energy = model.find_component('input_' + self.inputs[0] +
                                            '_' + self.name)
        output_energy = model.find_component('output_' + self.outputs[0] +
                                             '_' + self.name)
        floor_temp = model.find_component('floor_temp_' + self.name)
        area = model.find_component('size_' + self.name)

        temp_var = model.find_component('temp_' + self.name)
        return_temp_var = model.find_component('return_temp_' + self.name)
        average_t = model.find_component('average_t_' + self.name)
        heat_flux = model.find_component('heat_flux_' + self.name)
        room_temp = model.find_component('room_temp')
        co = model.find_component('co')

        for t in range(len(model.time_step)):
            if self.temp_profile[t] >= 15:
                model.cons.add(average_t[t + 1] == 0)
                model.cons.add(floor_temp[t + 1] == 0)
                model.cons.add(heat_flux[t + 1] == 0)
                model.cons.add(room_temp[t + 1] == 0)
                model.cons.add(return_temp_var[t + 1] == 0)
            else:
                model.cons.add(return_temp_var[t + 1] >= room_temp[t + 1])
                model.cons.add(average_t[t + 1] == (temp_var[t + 1] +
                                                    return_temp_var[t + 1]) / 2)
                model.cons.add(
                    floor_temp[t + 1] == 0.625 * average_t[t + 1] + 6.875
                    )
                model.cons.add(heat_flux[t + 1] == 8.92 * (
                        (
                                    floor_temp_approximate - room_temp_approximate) ** 1.1 +
                        1.1 *
                        (
                                    floor_temp_approximate - room_temp_approximate) ** 0.1 * (
                                floor_temp[
                                    t + 1] - floor_temp_approximate) - 1.1 *
                        (
                                    floor_temp_approximate - room_temp_approximate) ** 0.1 * (
                                room_temp[t + 1] - room_temp_approximate)))
            model.cons.add(
                input_energy[t + 1] * 1000 == heat_flux[t + 1] * area)
            print(self.temp_profile[t])
            model.cons.add(
                co[t + 1] * (21 - self.temp_profile[t]) ==
                (room_temp[t + 1] - self.temp_profile[t]))
            model.cons.add(
                input_energy[t + 1] == output_energy[t + 1] * co[t + 1])

    def _constraint_pmv(self, model):
        """
        Calculate the COP value in each time step, with default set
        temperature of 60 degree and machine efficiency of 40%.
        """
        pa = model.find_component('pa')
        pmv = model.find_component('pmv')
        room_temp = model.find_component('room_temp')
        for t in model.time_step:
            if self.temp_profile[t - 1] >= 15:
                model.cons.add(pmv[t] == -10)
                model.cons.add(pa[t] == -10)
            else:
                coeff = eval(b[t - 1])
                model.cons.add(
                    pa[t] == (85.165 * room_temp[t] - 539.063) / 1000)
                model.cons.add(pmv[t] <= 0.5)
                model.cons.add(pmv[t] >= -0.5)
                model.cons.add(pmv[t] == (coeff[0] * room_temp[t] +
                                          coeff[1] * pa[t] - coeff[2]))

    # def _constraint_mass_flow(self, model):
    #    for heat_input in self.heat_flows_in:
    #        m_in = model.find_component(heat_input[0] + '_' + heat_input[1] +
    #                                    '_' + 'mass')
    #        m_out = model.find_component(heat_input[1] + '_' + heat_input[0] +
    #                                     '_' + 'mass')
    #        for t in range(len(model.time_step)):
    #            model.cons.add(m_in[t + 1] == m_out[t + 1])

    # todo (qli):
    def _constraint_heat_water_return_temp(self, model, room_temp=21):
        return_temp_var = model.find_component('return_temp_' + self.name)
        for t in model.time_step:
            model.cons.add(room_temp <= return_temp_var[t])

    def add_cons(self, model):
        self._constraint_conver(model)
        self._constraint_temp(model)
        self._constraint_vdi2067(model)
        self._constraint_heat_inputs(model)
        if self.comfort_model:
            self._constraint_floor_temp(model)
            self._constraint_pmv(model)
            # self._constraint_heat_water_return_temp(model)

    def add_vars(self, model):
        super().add_vars(model)

        # todo (xzh): Add introduction for each variable. some variable are
        #  hard to understand!
        temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('temp_' + self.name, temp)

        return_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('return_temp_' + self.name, return_temp)

        floor_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('floor_temp_' + self.name, floor_temp)

        average_t = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('average_t_' + self.name, average_t)

        heat_flux = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('heat_flux_' + self.name, heat_flux)

        room_temp = pyo.Var(model.time_step, bounds=(0, None))
        model.add_component('room_temp', room_temp)

        pa = pyo.Var(model.time_step, bounds=(-10, None))
        model.add_component('pa', pa)

        pmv1 = pyo.Var(model.time_step, bounds=(None, None))
        model.add_component('pmv', pmv1)

        co = pyo.Var(model.time_step, bounds=(None, None))
        model.add_component('co', co)
