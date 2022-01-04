import os
import re
import pandas as pd

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def analysis_lp_file(file_path):
    f = open(file_path, "r+")
    f_temp = open("analysis_lp_temp.txt", "w+")
    f_new = open("analysis_lp_new.txt", "w+")

    lines = f.readlines()
    get_constrains(lines, f_temp)
    f_temp.close()

    f_temp = open("analysis_lp_temp.txt", "r+")
    new_lines = f_temp.readlines()
    del_duplicate(new_lines, f_new)

    f_new.close()


def get_constrains(lines, file_new):
    line_nr = 0
    while line_nr < len(lines):
        if lines[line_nr].startswith('c_'):
            file_new.write("\r\n")
        elif lines[line_nr].startswith('bounds'):
            break
        else:
            lines[line_nr] = re.sub(u"\\(.*?\\)", "", lines[line_nr])
            file_new.write(lines[line_nr].strip())
        line_nr += 1


def del_duplicate(lines, file_new):
    lines_seen = set()
    for line in lines:
        print(line)
        if line not in lines_seen:
            lines_seen.add(line)
            file_new.write(line)


if __name__ == "__main__":
    file_name = 'project_7_model.lp'
    file = os.path.join(base_path, 'data', 'opt_output', file_name)
    analysis_lp_file(file)
