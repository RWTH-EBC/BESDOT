# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
import os
import sphinx_rtd_theme


project = 'Besdot'
copyright = '2022, Yi Nie'
author = 'Yi Nie'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
model_path = os.path.join(base_path, 'scripts')
tool_path = os.path.join(base_path, 'utils')
#md_path = os.path.join(base_path, 'docs','Besdot 4b30fb98d32f4d768dbf30690bf2740e')

sys.path.insert(0, base_path)
# sys.path.insert(0, model_path)
# sys.path.insert(0, tool_path)

extensions = ['sphinx.ext.autodoc', 'myst_parser']

templates_path = ['_templates']
exclude_patterns = []

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

# multi-language docs
language = 'en'
locale_dirs = ['../locales/']   # path is example but recommended.
gettext_compact = False  # optional.
gettext_uuid = True  # optional.

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
# html_static_path = ['_static']
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
