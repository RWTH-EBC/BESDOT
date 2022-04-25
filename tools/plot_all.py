import os
import tools.post_solar_chp as post_pro

nr = 27
a = 8760
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
result_output_path = os.path.join(base_path, 'data', 'opt_output',
                                 + 'project_' + nr + '_result.csv')
post_pro.print_size(result_output_path)
post_pro.step_plot_two_lines(result_output_path, a, 'input_elec_e_grid',
                             'output_elec_e_grid', 'Input', 'Output',
                             'Energieaustausch des Stromgrids',
                             r'Leistung (kW)')

post_pro.step_plot_status(result_output_path, 1, a+1, 'status_chp',
                            'Status des BHKW', r'Status')

post_pro.step_plot_heat_demand_color(result_output_path, a)