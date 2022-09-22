import os
import tools.post_solar_chp as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plot_all(nr='_1', proNr=25, a=120, comp='s_hi', bld='wg'):
    result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                      'project_' + str(proNr) + '_result' + nr + '.csv')
    temp_output_path = os.path.join(base_path, 'data', 'cls_file',
                                      '6day_24hour_wg_qli_1.csv')

    post_pro.print_size(result_output_path)
    post_pro.step_plot_water_tes_demand(result_output_path, a, bld=bld)

    post_pro.step_plot_water_tes_wg_wp(result_output_path, a, bld=bld)
    post_pro.step_plot_heat_3(result_output_path, a, bld=bld)

    post_pro.step_plot_elec_e_grid_1(result_output_path, a, bld=bld)

    post_pro.step_plot_elec_bilanz_nwg_2(result_output_path, a, bld=bld, name=comp)
    post_pro.step_plot_one_line_nwg(result_output_path,a, 'tp_val_hw_e_boi_temp','temp',

                                 r"Temperatur ($^\circ$C)", bld=bld)

    post_pro.step_plot_two_lines(result_output_path, a,'water_tes_tp_val_hw_mass', 'tp_val_hw_e_boi_mass',
                                 'Massenstrom vom SP zum DWV','Massenstrom vom DWV zum EHK', '1', r'Massenstrom (kg/h)', bld=bld)
    post_pro.step_plot_two_lines(result_output_path, a,'water_tes_tp_val_therm_mass', 'tp_val_therm_therm_cns_mass',
                                 'Massenstrom vom SP zum DWV','Massenstrom vom DWV zum HK', '2', r'Massenstrom (kg/h)', bld=bld)
    post_pro.step_plot_one_line(result_output_path,a, 'tp_val_therm_therm_cns_mass', 'Massenstrom im Heizkörper',
                               r'Massenstrom (kg/h)', bld=bld)
    post_pro.step_plot_heat_demand_color_wg_1(result_output_path, a, bld=bld,proNr=proNr)

plot_all(nr='_wp1', proNr=26, a=192, bld='nwg_wp2')

