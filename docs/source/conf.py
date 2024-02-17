import re

project = 'Litemapy'
copyright = '2022, Smyler and Litemapy contributors'
author = 'Smyler and Litemapy contributors'

# Read version from project files,
# we don't import it like we do in setup.py because RTD takes care of it and we don't want to interfere
with open("../../litemapy/info.py") as f:
    match = re.search(r'LITEMAPY_VERSION = "(.+)"', f.read())
    assert match != None
    version = match[1]

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
    'nbtlib': ('https://vberlier.github.io/nbtlib/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# Include __init__ doc in class doc
autoclass_content = 'both'

exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']