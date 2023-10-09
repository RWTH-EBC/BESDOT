import os
import pandas as pd
from utils.calc_annuity_vdi2067 import calc_annuity

# Get the path of the current script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, '..', 'data', 'opt_output', 'project_12',
                             'project_12_city_subsidy_test_stuttgart_chp', 'result.csv')
df = pd.read_csv(csv_file_path)

# Read the values from the CSV file
annual_cost_value = df.loc[df['var'] == 'annual_cost_bld_12[None]', 'value'].values[0]
operation_cost_value = df.loc[df['var'] == 'operation_cost_bld_12[None]', 'value'].values[0]
total_revenue_value = df.loc[df['var'] == 'total_revenue_bld_12[None]', 'value'].values[0]
other_op_cost_value = df.loc[df['var'] == 'other_op_cost_bld_12[None]', 'value'].values[0]
print("Value corresponding to 'annual_cost_bld_12[None]':", annual_cost_value)
print("Value corresponding to 'operation_cost_bld_12[None]':", operation_cost_value)
print("Value corresponding to 'total_revenue_bld_12[None]':", total_revenue_value)
print("Value corresponding to 'other_op_cost_bld_12[None]':", other_op_cost_value)

# Read investment values
invest_chp_value = df.loc[df['var'] == 'invest_chp[None]', 'value'].values[0]
invest_pv_value = df.loc[df['var'] == 'invest_pv[None]', 'value'].values[0]
invest_water_tes_value = df.loc[df['var'] == 'invest_water_tes[None]', 'value'].values[0]
print("Value of 'invest_chp[None]':", invest_chp_value)
print("Value of 'invest_pv[None]':", invest_pv_value)
print("Value of 'invest_water_tes[None]':", invest_water_tes_value)

# Calculate annuities
t_n_chp = 15
f_inst_chp = 0.05
f_w_chp = 0.015
f_op_chp = 20

annuity_chp = calc_annuity(t_n_chp, invest_chp_value, f_inst_chp, f_w_chp, f_op_chp)

t_n = 20
f_inst = 0.01
f_w = 0.015
f_op = 20

annuity_pv = calc_annuity(t_n, invest_pv_value, f_inst, f_w, f_op)
annuity_water_tes = calc_annuity(t_n, invest_water_tes_value, f_inst, f_w, f_op)

print("Annuity of 'invest_chp':", annuity_chp)
print("Annuity of 'invest_pv':", annuity_pv)
print("Annuity of 'invest_water_tes':", annuity_water_tes)

# Calculate the original total annual cost
original_total_annual_cost = operation_cost_value + other_op_cost_value - total_revenue_value\
                    + annuity_chp + annuity_pv + annuity_water_tes

print("Value of 'original_total_annual_cost':", original_total_annual_cost)

# Calculate the difference between annual_cost and original_annual_cost
difference = original_total_annual_cost - annual_cost_value

print("Difference between 'annual_cost' and 'original_annual_cost':", difference)

# Create a DataFrame to hold the results in a vertical format
results = pd.DataFrame({
    'Variable': ['operation_cost', 'total_revenue', 'other_op_cost',
                 'invest_chp', 'invest_pv', 'invest_water_tes', 'annuity_chp', 'annuity_pv',
                 'annuity_water_tes', 'annual_cost', 'original_annual_Cost', 'difference'],
    'Value': [operation_cost_value, total_revenue_value, other_op_cost_value,
              invest_chp_value, invest_pv_value, invest_water_tes_value, annuity_chp, annuity_pv,
              annuity_water_tes, annual_cost_value, original_total_annual_cost, difference]
}).set_index('Variable')

# Save the DataFrame to a CSV file
results.to_csv('results.csv')

print("Results saved to 'results.csv'")
