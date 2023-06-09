import os
import utils.post_solar_chp as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plot_all(nr='_1', proNr=25, a=120, comp='s_hi', bld='wg'):
    result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                      'project_' + str(proNr) + '_result' + nr + '.csv')

    post_pro.print_size(result_output_path)
    post_pro.step_plot_heat_demand_color_nwg(result_output_path, a, bld=bld)

    post_pro.step_plot_status(result_output_path, 1, a + 1, bld=bld, name=comp)
    post_pro.step_plot_heat_demand_color_nwg(result_output_path, a, bld=bld)
    post_pro.step_plot_elec_e_grid(result_output_path, a, bld=bld)

    post_pro.step_plot_elec_bilanz_nwg(result_output_path, a, bld=bld, name=comp)

    post_pro.step_plot_two_lines(result_output_path, a,'boi_s_tp_val_therm_mass', 'tp_val_therm_therm_cns_mass',
                                 'Massenstrom vom HK zum DWV','Massenstrom im Heizkörper', '1', r'Leistung (kW)', bld=bld)
    post_pro.step_plot_one_line(result_output_path, a,'boi_s_tp_val_therm_mass',
                                 'Massenstrom vom HK zum DWV', r'Massenstrom (kg/h)', bld=bld)
    post_pro.step_plot_one_line(result_output_path,a, 'tp_val_therm_therm_cns_mass', 'Massenstrom im Heizkörper',
                               r'Leistung (kW)', bld=bld)
    post_pro.step_plot_water_tes_demand_nwg_qli(result_output_path, a, bld=bld)

plot_all(nr='_nwg', proNr=26, a=192, comp='_s', bld='nwg')

