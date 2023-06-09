import os
import utils.post_solar_chp as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plot_all(nr='_1', proNr=25, a=120, comp='s_hi', bld='wg'):
    result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                      'project_' + str(proNr) + '_result' + nr + '.csv')

    post_pro.print_size(result_output_path)
    post_pro.step_plot_heat_demand_color(result_output_path, a, bld=bld, proNr=proNr)
    if comp == '':
        post_pro.step_plot_elec_ein_aus(result_output_path, a, bld=bld)

        #todo: Wer hat Versorgungsvorhang Netz oder BAT
        #post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_bat',
                                     #'output_elec_e_grid', 'BAT Input', 'Netz Output',
                                     #'Energie', r'Leistung (kW)', bld=bld)
        #post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_bat',
                                     #'output_elec_pv', 'BAT Input', 'PV Output',
                                     #'Energ', r'Leistung (kW)', bld=bld)
        post_pro.step_plot_two_lines(result_output_path, a, 'heat_water_tes_tp_val_hw',
                                     'input_heat_hw_cns', 'heat_water_tes_tp_val', 'input_heat_hw_cns',
                                     'eg',
                                     r'Leistung (kW)', bld=bld)
        #post_pro.step_plot_tp_val(result_output_path, a, bld=bld, name='')
        post_pro.step_plot_hw(result_output_path, a, bld=bld)
        post_pro.step_plot_hw_cns(result_output_path, a, bld=bld)
        post_pro.step_plot_water_tes_demand(result_output_path, a, bld=bld)
        post_pro.step_plot_demand_e_boi(result_output_path, a, bld=bld)

        post_pro.step_plot_water_tes(result_output_path, a, bld=bld)
        post_pro.step_plot_heat_1(result_output_path, a, bld=bld)

        post_pro.step_plot_elec_1(result_output_path, a, bld=bld)


    else:
        post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_e_grid',
                                     'output_elec_e_grid', 'Input', 'Output',
                                     'Energieaustausch des Stromgrids',
                                     r'Leistung (kW)', bld=bld)

        post_pro.step_plot_status(result_output_path, 1, a + 1, bld=bld, name=comp)

        post_pro.step_plot_heat_demand_color_11(result_output_path, a, bld=bld)
        post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_e_grid',
                                     'output_elec_e_grid', 'Input', 'Output',
                                     'Energieaustausch des Stromgrids',
                                     r'Leistung (kW)', bld=bld)

        post_pro.step_plot_four_lines(result_output_path, a,
                                      'output_heat_chp',
                                      'output_heat_boi_s', 'output_heat_heat_pump',
                                      'input_heat_therm_cns', 'Wärme aus BHKW',
                                      'Wärme aus Kessel', 'Warmwasserbedarf',
                                      'Wärmebedarf',
                                      'Energieerzeugung', r'Leistung (kW)', bld=bld, n=1.5)
        
        post_pro.step_plot_chp_water_tes_color(result_output_path, a, bld=bld, name=comp)

        post_pro.step_plot_heat_speicher(result_output_path, a, bld=bld, name=comp)
        post_pro.step_plot_elec_1(result_output_path, a, bld=bld)
        post_pro.step_plot_elec_bilanz(result_output_path, a, bld=bld, name=comp)
        post_pro.step_plot_chp_last(result_output_path, a, bld=bld, name=comp)

        if comp == '_s':
            post_pro.step_plot_one_line(result_output_path, a, 'therm_eff_chp',
                                        'Thermische Effizienz', r'Effizienz', bld=bld,
                                        n=1.02)
        if comp == '_s_hi':
            pass

        if comp == '_b':
            post_pro.step_plot_one_line(result_output_path, a, 'therm_eff_chp',
                                        'Thermische Effizienz', r'Effizienz', bld=bld,
                                        n=1.02)
plot_all(nr='_7', proNr=26, a=192, comp='_s_hi', bld='nwg')
#plot_all(nr='', proNr=25, a=120, comp='')
# - check
