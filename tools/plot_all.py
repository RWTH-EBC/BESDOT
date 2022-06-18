import os
import tools.post_solar_chp as post_pro

name = 's_hi'
a = 120
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def plot_all(nr):
    result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                      'project_27_result_'+nr+'.csv')

    post_pro.print_size(result_output_path)
    post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_e_grid',
                                 'output_elec_e_grid', 'Input', 'Output',
                                 'Energieaustausch des Stromgrids',
                                 r'Leistung (kW)')

    #post_pro.step_plot_status(result_output_path, 1, a + 1, 'status_chp',
                              #'Status des BHKW', r'Status')

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

    post_pro.step_plot_three_lines(result_output_path, a, 'temp_water_tes',
                                   'inlet_temp_chp','outlet_temp_chp',
                                   'temp_water_tes', 'Inlet', 'Outlet',
                                   'Temperatur',
                                    r'Temperatur ($^\circ$C)', n=1.05)

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

    if name == 's':
        post_pro.step_plot_one_line(result_output_path, a, 'therm_eff_chp',
                                    'Thermische Effizienz', r'Effizienz',
                                    n=1.02)
    if name == 's_hi':
        pass
    if name == 'b':
        post_pro.step_plot_one_line(result_output_path, a, 'therm_eff_chp',
                                    'Thermische Effizienz', r'Effizienz',
                                    n=1.02)
plot_all('')