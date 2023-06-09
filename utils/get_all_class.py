#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Created by jgn on 30.11.2020.

import os, sys
import inspect
import importlib

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_all_class_from_modules(module_list):
    class_list = {}
    for module in module_list:
        for name, obj in inspect.getmembers(module, inspect.isclass):
            class_list[name] = obj
    return class_list


def get_all_modules(modules_path_list, package):
    all_modules = []
    for path in modules_path_list:
        module = importlib.import_module(path, package=package)
        all_modules.append(module)
    return all_modules


def get_all_modules_path(directory):
    all_modules_path = []
    for file in os.listdir(directory):
        if file.endswith('.py') and file != '__init__.py':
            path = os.path.join(directory, file)
            path = path.replace(directory, '')
            path = path.replace(os.sep, '.')
            path = path[:-3]
            all_modules_path.append(path)
    all_modules_path = list(set(all_modules_path))
    return all_modules_path


def run():
    """
    This function go through the given directory and search all component models and return them in a dictionary.
    Parameters
    ----------
    directory: The abs. path of component library

    Returns
    -------
    A dictionary with all component names as keys and component classes as values
    """
    package = 'scripts.components'
    directory = os.path.join(base_path, 'scripts', 'components')
    sys.path.append(directory)
    all_modules_path = get_all_modules_path(directory)
    all_modules = get_all_modules(all_modules_path, package)
    class_list = get_all_class_from_modules(all_modules)
    return class_list


if __name__ == '__main__':
    print(run())
