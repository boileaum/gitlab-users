# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# set of options see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from gitlab_users import __version__

project = "gitlab-users"
copyright = "2025 Matthieu Boileau"
author = "Matthieu Boileau"

release = __version__

extensions = [
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx_autodoc_typehints",
]


html_theme = "furo"
add_module_names = False

# Enable automatic summary tables for modules/classes/functions
autosummary_generate = True

autoclass_content = "class"

# Exclude __init__ from class documentation, but include all public methods
autodoc_default_options = {
    "undoc-members": False,
    "private-members": False,
    "exclude-members": "__init__",
    "inherited-members": True,  # inclut les méthodes héritées
}
autodoc_typehints = "description"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Napoleon settings for Google-style docstrings and unified return/argument type display
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_return_type = True
napoleon_use_rtype = False

# modindex_common_prefix = ["gitlab_users."]
toc_object_entries_show_parents = "hide"
