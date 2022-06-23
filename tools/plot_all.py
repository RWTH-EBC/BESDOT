import os
import tools.post_solar_chp as post_pro

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plot_all(nr='_1', proNr=25, a=120, comp='s_hi'):
    result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                      'project_' + str(proNr) + '_result' + nr + '.csv')

    post_pro.print_size(result_output_path)
    if comp == '':
        post_pro.step_plot_one_line(result_output_path, a, 'temp_water_tes', 'Speichertemperatur',
                                    r'Temperatur ($^\circ$C)')
        post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_e_grid',
                                     'output_elec_e_grid', 'Input', 'Output',
                                     'Energieaustausch des Stromgrids',
                                     r'Leistung (kW)')
        # post_pro.step_plot_heat_demand_color(result_output_path, a)
        post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_e_grid',
                                     'output_elec_e_grid', 'Input', 'Output',
                                     'Energieaustausch des Stromgrids',
                                     r'Leistung (kW)')
        # post_pro.step_plot_heat(result_output_path, a)

        # post_pro.step_plot_heat_water_tes(result_output_path, a)
        # post_pro.step_plot_heat_speicher(result_output_path, a)
        # post_pro.step_plot_elec(result_output_path, a)
        # post_pro.step_plot_elec_bilanz(result_output_path, a)

    else:
        post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_e_grid',
                                     'output_elec_e_grid', 'Input', 'Output',
                                     'Energieaustausch des Stromgrids',
                                     r'Leistung (kW)')

        post_pro.step_plot_status(result_output_path, 1, a + 1, 'status_chp',
                                  'Status des BHKW', r'Status')

        post_pro.step_plot_heat_demand_color(result_output_path, a)
        post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_e_grid',
                                     'output_elec_e_grid', 'Input', 'Output',
                                     'Energieaustausch des Stromgrids',
                                     r'Leistung (kW)')

        post_pro.step_plot_four_lines(result_output_path, a,
                                      'output_heat_chp',
                                      'output_heat_boi_s', 'input_heat_hw_cns',
                                      'input_heat_therm_cns', 'Wärme aus BHKW',
                                      'Wärme aus Kessel', 'Warmwasserbedarf',
                                      'Wärmebedarf',
                                      'Energieerzeugung', r'Leistung (kW)', n=1.5)

        #post_pro.step_plot_three_lines(result_output_path, a, 'temp_water_tes',
                                       #'inlet_temp_chp', 'outlet_temp_chp',
                                       #'temp_water_tes', 'Inlet', 'Outlet',
                                       #'Temperatur',
                                       #r'Temperatur ($^\circ$C)', n=1.05)

        post_pro.step_plot_status(result_output_path, 1, a + 1, 'status_chp',
                                  'Status des BHKW', r'Status')

        post_pro.step_plot_chp_color(result_output_path, a)

        post_pro.step_plot_chp_diagram_color(result_output_path, a)
        post_pro.step_plot_chp_energy_color(result_output_path, a)
        post_pro.step_plot_chp_water_tes_color(result_output_path, a)
        post_pro.step_plot_heat(result_output_path, a)
        post_pro.step_plot_chp_diagram_color1(result_output_path, a)

        post_pro.step_plot_heat_water_tes(result_output_path, a)
        post_pro.step_plot_heat_speicher(result_output_path, a)
        post_pro.step_plot_elec(result_output_path, a)
        post_pro.step_plot_elec_bilanz(result_output_path, a)
        post_pro.step_plot_chp_last(result_output_path, a)

        if comp == 's':
            post_pro.step_plot_one_line(result_output_path, a, 'therm_eff_chp',
                                        'Thermische Effizienz', r'Effizienz',
                                        n=1.02)
        if comp == 's_hi':
            pass
        if comp == 'b':
            post_pro.step_plot_one_line(result_output_path, a, 'therm_eff_chp',
                                        'Thermische Effizienz', r'Effizienz',
                                        n=1.02)
plot_all(nr='', proNr=25, a=120, comp='s_hi')
