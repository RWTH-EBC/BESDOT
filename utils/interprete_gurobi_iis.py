# interpretes the infeasible set of constraints and variables returned by gurobi
import os
import re


# 查找两个文件中变量的映射关系
def map_variables(file1, file2):
    # file1 is the raw model file and file2 is the model file with names
    # Initialize dictionaries to hold variables and constraints
    vars= {}

    # Define regex patterns for variable and constraint
    raw_var_pattern = re.compile(
        r'[-+]?\d+\s*<=\s*(x\d+)\s*<=\s*([-+]?inf|\d+)')
    name_var_pattern = re.compile(r'<=\s*(.+)\s*<=')

    # Initialize a flag for bounds
    bounds_flag = False

    # Open both files
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        # Iterate over both files line by line
        for line1, line2 in zip(f1, f2):
            # Check if the line is "bounds"
            if "bounds" in line1:
                bounds_flag = True
                continue

            # Only perform regex matching after "bounds"
            if bounds_flag:
                var_match1 = raw_var_pattern.search(line1)
                var_match2 = name_var_pattern.search(line2)

                if var_match1:
                    vars[var_match1.group(1)] = var_match2.group(1)
        # print(vars)
    return vars


# 查找两个文件中约束的映射关系
def map_constraints(file1, file2):
    # file1 is the raw model file and file2 is the model file with names
    # Initialize dictionaries to hold variables and constraints
    constraints = {}

    # Define regex patterns for variable and constraint
    raw_con_pattern = re.compile(r'^(c_.+):')

    # Open both files
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        # Iterate over both files line by line
        for line1, line2 in zip(f1, f2):
            con_match1 = raw_con_pattern.search(line1)
            if con_match1:
                # print(con_match1.group(1))
                constraints[con_match1.group(1)] = line2.strip()
        # print(constraints)
    return constraints


# 检查两个文件行数是否相同
def check_line_count(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        count1 = 0
        count2 = 0
        for line1, line2 in zip(f1, f2):
            count1 += 1
            count2 += 1

    if count1 == count2:
        print('The number of lines in both files are the same')
    else:
        print('Wrong with the files, the number of lines are different')

    return count1 == count2


# 检查文件file1，当file1中的变量在vars_map中时，检查对应字典中的值是否在file2中
def check_variables(file1, file2, vars_map):
    # Define regex patterns for variable and constraint
    var_pattern = re.compile(r'(x\d+)')
    line_pattern = re.compile(r'([-+]\d+\s*x\d+)')

    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        for line1, line2 in zip(f1, f2):
            # 检查line1中的变量是否在vars_map的key中
            var_match1 = line_pattern.search(line1)
            if var_match1:
                var = var_pattern.search(var_match1.group())
                if var:
                    var_str = var.group()  # 获取匹配的字符串
                    print(var_str)
                    if var_str in vars_map:
                        print(vars_map[var_str])
                        if vars_map[var_str] not in line2:
                            print(f'Variable {var_str} is not mapped correctly')
                            return False


# 对一个文件进行检查，检查文件中的约束是否在cons_map中，如果在，则将这个约束的值替换为
# cons_map中对应的value；再检查文件中的变量是否在vars_map中，如果在，则将这个变量的值替换为
# vars_map中对应的value。最后将修改后的内容保存在一个新文件中
def check_constraints(file, cons_map, vars_map):
    # Define regex patterns for variable and constraint
    var_pattern = re.compile(r'(x\d+)')
    cons_pattern = re.compile(r'(c_.+):')

    new_file = file.replace('.ilp', '_new.ilp')
    with open(file, 'r') as f, open(new_file, 'w') as new_f:
        for line in f:
            # 检查line中的约束是否在cons_map的key中
            cons_match = cons_pattern.search(line)
            if cons_match:
                cons = cons_match.group(1)
                if cons in cons_map:
                    line = line.replace(cons, cons_map[cons])

            # 检查line中的变量是否在vars_map的key中
            var_match = var_pattern.findall(line)
            if var_match:
                for var in var_match:
                    if var in vars_map:
                        line = line.replace(var, vars_map[var])

            new_f.write(line)

    return new_file


if __name__ == '__main__':
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_path, 'data', 'opt_output', 'project_4_2',
                              'model.lp')
    raw_model_path = os.path.join(base_path, 'data', 'opt_output',
                                  'project_4_2', 'raw_model.lp')
    iis_path = os.path.join(base_path, 'data', 'opt_output', 'project_4_2',
                            'iis.ilp')

    if check_line_count(raw_model_path, model_path):
        vars_map = map_variables(raw_model_path, model_path)
        cons_map = map_constraints(raw_model_path, model_path)
        new_file = check_constraints(iis_path, cons_map, vars_map)
