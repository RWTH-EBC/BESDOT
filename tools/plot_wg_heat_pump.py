import os
import tools.post_solar_chp as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plot_all(nr='_1', proNr=25, a=120, comp='s_hi', bld='wg_heat_pump'):
    result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                      'project_' + str(proNr) + '_result' + nr + '.csv')

    post_pro.print_size(result_output_path)
    #post_pro.step_plot_heat_demand_color_wg(result_output_path, a, bld=bld, proNr=proNr)

    #post_pro.step_plot_hw(result_output_path, a, bld=bld)
    #post_pro.step_plot_demand_e_boi(result_output_path, a, bld=bld)

    post_pro.step_plot_heat_2(result_output_path, a, bld=bld)

    post_pro.step_plot_elec_2(result_output_path, a, bld=bld)
    post_pro.step_plot_elec_1(result_output_path, a, bld=bld)
    post_pro.step_plot_elec_e_grid_wg(result_output_path, a, bld=bld)
    post_pro.step_plot_water_tes_demand_wg_heat_pump(result_output_path, a, bld=bld)


plot_all(nr='_wp', proNr=25, a=120, comp='')

