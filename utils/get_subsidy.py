import os
import numpy as np
import pandas as pd

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSIDY_PATH = os.path.join(base_path, 'data', 'subsidy', 'subsidy.csv')
subsidy_df = pd.read_csv(SUBSIDY_PATH)


def find_subsidies(city, state, country=None, user='basic', building='all'):
    """find the subsidies for the city, state and country"""
    # the subsidies for the country, in the actual case, it is Germany
    all_country_sub = subsidy_df[subsidy_df['level'] == 'country']

    # the subsidies for the state
    all_state_sub = subsidy_df[subsidy_df['level'] == 'state']
    state_sub = all_state_sub[all_state_sub['name'].str.contains(state)]

    # the subsidies for the city
    all_city_sub = subsidy_df[subsidy_df['level'] == 'city']
    city_sub = all_city_sub[all_city_sub['name'].str.contains(city)]

    all_sub = pd.concat([all_country_sub, state_sub, city_sub])
    valid_sub = all_sub[(all_sub['user'] == user) &
                        ((all_sub['building'] == building) |
                         (all_sub['building'] == 'all'))]

    return valid_sub


def check_subsidy(sub_name):
    """check if the subsidy is for building or for components"""
    subsidy = subsidy_df[subsidy_df['name'] == sub_name]
    bld_sub = subsidy[subsidy['apply'].str.contains('building')]
    # user_sub = subsidy[subsidy['user']]
    sub_dict = {}

    # add the apply type to the dictionary
    if bld_sub.shape[0] == 0:
        sub_dict['apply'] = ['component']
    elif bld_sub.shape[0] == subsidy.shape[0]:
        sub_dict['apply'] = ['building']
    else:
        sub_dict['apply'] = ['building', 'component']

    return sub_dict['apply']


def find_dependent_vars(sub_name, sub_type, apply_for):
    """find the dependent variables of the subsidy. The dependent variables
    of the subsidy could be investment, size or area and for different user
    or building type the dependent variables are usually same. So that the
    check of the dependent variables is only needed for the first time."""
    sub_detail = subsidy_df[(subsidy_df['name'] == sub_name) & (subsidy_df[
        'apply'] == apply_for) & (subsidy_df['type'] == sub_type)]

    if sub_detail['Invest Coefficient'].notnull().any():
        # print('The subsidy {} is for investment'.format(sub_name))
        return 'investment'
    if sub_detail['Size Coefficient'].notnull().any():
        # print('The subsidy {} is for size'.format(sub_name))
        return 'size'
    if sub_detail['Area Coefficient'].notnull().any():
        # print('The subsidy {} is for area'.format(sub_name))
        return 'area'
    if sub_detail['Demand Coefficient'].notnull().any():
        # print('The subsidy {} is for demand'.format(sub_name))
        return 'demand'


def find_sub_rules(sub_name, sub_type, apply_for, user='basic',
                   building='all', dependent_vars=None):
    """find the rules of the subsidy."""
    sub_detail = subsidy_df[(subsidy_df['name'] == sub_name) & (subsidy_df[
        'apply'] == apply_for) & (subsidy_df['type'] == sub_type) & (subsidy_df[
        'user'] == user) & ((subsidy_df['building'] == building) | (
            subsidy_df['building'] == 'all'))]
    if dependent_vars is None:
        dependent_vars = find_dependent_vars(sub_name, sub_type, apply_for)

    rule = find_rules_from_df(sub_detail, dependent_vars)

    return rule


def find_sub_modes(sub_name, sub_type, apply_for, user='basic',
                   building='all'):
    """find the modes of the subsidy for operate subsidy."""
    mode_detail = subsidy_df[(subsidy_df['name'] == sub_name) & (subsidy_df[
        'apply'] == apply_for) & (subsidy_df['type'] == sub_type) & (subsidy_df[
        'user'] == user) & ((subsidy_df['building'] == building) | (
            subsidy_df['building'] == 'all')) & (subsidy_df['mode'].notnull())]
    # print(mode_detail['mode'].unique())
    return mode_detail['mode'].unique()


def find_mode_rules(sub_name, sub_type, apply_for, mode, user='basic',
                    building='all', dependent_vars=None):
    """find the rules of the different mode of subsidy."""
    mode_detail = subsidy_df[(subsidy_df['name'] == sub_name) & (subsidy_df[
        'apply'] == apply_for) & (subsidy_df['type'] == sub_type) & (subsidy_df[
        'user'] == user) & ((subsidy_df['building'] == building) | (
            subsidy_df['building'] == 'all')) & (subsidy_df['mode'] == mode)]
    if dependent_vars is None:
        dependent_vars = find_dependent_vars(sub_name, sub_type, apply_for)

    rule = find_rules_from_df(mode_detail, dependent_vars)
    return rule


def find_rules_from_df(sub_df, dependent_vars):
    rule = []
    if dependent_vars == 'investment':
        for index, row in sub_df.iterrows():
            rule.append({'lower': row['Invest Lower'],
                         'upper': row['Invest Upper'],
                         'coefficient': row['Invest Coefficient'],
                         'constant': row['Invest Constant']})
    elif dependent_vars == 'size':
        for index, row in sub_df.iterrows():
            rule.append({'lower': row['Size Lower'],
                         'upper': row['Size Upper'],
                         'coefficient': row['Size Coefficient'],
                         'constant': row['Size Constant']})
    elif dependent_vars == 'area':
        for index, row in sub_df.iterrows():
            rule.append({'lower': row['Area Lower'],
                         'upper': row['Area Upper'],
                         'coefficient': row['Area Coefficient'],
                         'constant': row['Area Constant']})
    elif dependent_vars == 'demand':
        for index, row in sub_df.iterrows():
            rule.append({'lower': row['Size Lower'],
                         'upper': row['Size Upper'],
                         'coefficient': row['Demand Coefficient'],
                         'constant': row['Demand Constant']})
    return rule
