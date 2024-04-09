"""
Tools to analyse the output csv file after optimization.
"""

import os
import math
import pandas as pd
import numpy as np


def find_element(output_df):
    """find all elements in dataframe, the variables with same name but
    different time step would be stored in a list"""
    output_df['var_pre'] = output_df['var'].map(lambda x: x.split('[')[0])
    all_elements = output_df['var_pre'].tolist()
    element_list = list(set(all_elements))  # delete duplicate elements

    elements_dict = {}
    for element in element_list:
        element_df = output_df.loc[output_df['var_pre'] == element]
        values = element_df['value'].tolist()
        elements_dict[element] = values

    return elements_dict


def find_size(csv_file):
    """
    Search for the results of each component in csv file.
    """
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    size_dict = {}
    for element in elements_dict:
        if len(elements_dict[element]) == 1:
            if 'size' in element and not np.isnan(elements_dict[element][0]):
                size_dict[element] = elements_dict[element][0]
                print('The size of', element, 'is', size_dict[element])
            if 'volume' in element and not np.isnan(
                    elements_dict[element][0]):
                size_dict[element] = elements_dict[element][0]
                print('The volume of', element, 'is', size_dict[element])


def sum_flow(csv_file, flow_name):
    """
    Calculate the sum of a specific energy flow in result file.
    """
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    flow_list = elements_dict[flow_name]
    print(sum(flow_list))


def find_max_timestep(csv_file, profile_name):
    """Search the maximal value of a profile and return the timestep of the
    maximal value. This function could be used to analysis the situation,
    how the peak demand is filled.
    Using find_element().keys() to find the name of the wanted profile"""
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    profile = elements_dict[profile_name]
    max_value = max(profile)
    index_max = profile.index(max(profile))

    return max_value, index_max


def save_timeseries(csv_file, name=''):
    """Take the time series from output file and save them as an individual
    csv file, to reduce the analysis time cost."""
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)

    element_len_set = set()
    for item in elements_dict.keys():
        if len(elements_dict[item]) > 1:
            # new_df = pd.DataFrame(index=range(len(elements_dict[item])))
            element_len_set.add(len(elements_dict[item]))

    # find the minimal length (greatest common divisor) of the time series
    gcd_result = element_len_set.pop()
    while element_len_set:
        num = element_len_set.pop()
        gcd_result = math.gcd(gcd_result, num)
    new_df = pd.DataFrame(index=range(gcd_result))

    for item in elements_dict.keys():
        if len(elements_dict[item]) > 1:
            if 'status' in item:  # quick fix for status in chp, need to
                # be fixed in the future
                pass
            elif 'building_connect' in item:
                pass
            elif 'energy_edge' in item:
                pass
            elif 'energy_on_edges' in item:
                pass
            elif len(elements_dict[item]) != gcd_result and len(elements_dict[
                item]) % gcd_result == 0:
                # nr = int(len(elements_dict[item]) / gcd_result)
                # for i in range(nr):
                #     new_df[item + '_' + str(i)] = elements_dict[item][i::nr]
                pass
            else:
                new_df[item] = elements_dict[item]

    output_path = os.path.split(csv_file)
    timeseries_path = os.path.join(output_path[0], name + '_timeseries.xlsx')
    new_df.to_excel(timeseries_path)


def save_non_time_series(csv_file, name=''):
    """Take the non time series from output file and save them as an individual
    csv file, to reduce the analysis time cost."""
    output_df = pd.read_csv(csv_file)
    elements_dict = find_element(output_df)
    new_df = pd.DataFrame()

    for item in elements_dict.keys():
        if len(elements_dict[item]) == 1:
            new_df[item] = elements_dict[item]

    new_df = new_df.T

    # print(new_df)
    output_path = os.path.split(csv_file)
    non_timeseries_path = os.path.join(output_path[0],
                                       name + '_non_timeseries.xlsx')
    new_df.to_excel(non_timeseries_path)


def csv_to_excel(project_path):
    """Convert result csv file in the folder to excel file for better
    understanding."""
    bld_path = os.path.join(project_path, 'result.csv')
    bld_timeseries_path = os.path.join(project_path, 'bld_timeseries.xlsx')
    bld_non_timeseries_path = os.path.join(project_path,
                                           'bld_non_timeseries.xlsx')

    if not os.path.exists(bld_timeseries_path):
        save_timeseries(bld_path, 'bld')
    if not os.path.exists(bld_non_timeseries_path):
        save_non_time_series(bld_path, 'bld')


def split_excel(excel_file):
    # 读取Excel文件
    xls = pd.ExcelFile(excel_file)
    sheet_to_df_map = pd.read_excel(xls, sheet_name=None)

    # 创建新的sheets
    input_df = pd.DataFrame()
    output_df = pd.DataFrame()

    # 遍历每一个sheet
    for sheet_name, df in sheet_to_df_map.items():
        # 创建一个新的DataFrame来保存每一列的和和最大值
        summary_df = pd.DataFrame(index=['Sum', 'Max'])

        # 遍历每一列
        for column in df.columns:
            # 求和和求最大值
            sum_val = df[column].sum()
            max_val = df[column].max()

            # 将求和和最大值结果保存到summary_df中
            summary_df[column] = pd.Series({'Sum': sum_val, 'Max': max_val})

        # 将summary_df追加到原始的df中
        df = pd.concat([df, summary_df])

        # 遍历每一列
        for column in df.columns:
            # 求和和求最大值
            sum_val = df[column].sum()
            max_val = df[column].max()

            # 如果最大值和求和结果都为0，删除该列
            if sum_val == 0 and max_val == 0:
                df = df.drop(columns=[column])
            # 如果列名以“input”开头，将该列移动到名为“input”的新sheet中
            elif column.startswith('input'):
                input_df[column] = df[column]
                df = df.drop(columns=[column])
            # 如果列名以“output”开头，将该列移动到名为“output”的新sheet中
            elif column.startswith('output'):
                output_df[column] = df[column]
                df = df.drop(columns=[column])

        # 保存处理后的sheet
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a',
                            if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name)

    # 保存新的sheets
    with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a',
                        if_sheet_exists='replace') as writer:
        input_df.to_excel(writer, sheet_name='input')
        output_df.to_excel(writer, sheet_name='output')


if __name__ == '__main__':
    # Provide the name of the project
    project_name = 'project_6'

    # The path of the project
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prj_result = os.path.join(base_path, 'data', 'opt_output', project_name)

    csv_to_excel(prj_result)
    split_excel(os.path.join(prj_result, 'bld_timeseries.xlsx'))

