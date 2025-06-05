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
]

# MyST parser configuration
myst_enable_extensions = [
    "strikethrough",
    "tasklist",
]

# Configure MyST link handling
myst_all_links_external = False
myst_url_schemes = ("http", "https", "mailto", "ftp")

# Suppress MyST warnings for cross-references to local markdown files
suppress_warnings = ["myst.xref_missing"]

html_theme = "furo"
add_module_names = False

# Enable automatic summary tables for modules/classes/functions
autosummary_generate = True

# Enable type hints in the documentation
autodoc_typehints = "signature"  # Show types in function signature only
autodoc_typehints_format = "short"  # Use short type names
autodoc_typehints_description_target = "documented"  # Only documented
typehints_fully_qualified = False
always_document_param_types = False
# Control the order of documented members in autodoc
autodoc_member_order = "bysource"

# Exclude __init__ from class documentation, but include all public methods
autodoc_default_options = {
    "undoc-members": False,
    "private-members": False,
    "inherited-members": True,  # inclut les méthodes héritées
    "member-order": "bysource",  # Preserve source order for individual modules
}

# Prevent duplicate return type sections
autodoc_preserve_defaults = True

# Control the order of documented members
autodoc_member_order = "bysource"  # Preserve source code order

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Napoleon settings for Google-style docstrings and unified return/argument type display
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_return_type = False  # Don't include return type from Napoleon
napoleon_use_rtype = False  # No separate :rtype: section
napoleon_use_param = True
napoleon_attr_annotations = True
napoleon_preprocess_types = False  # Don't process types in docstrings
napoleon_use_ivar = True
napoleon_custom_sections = None  # Don't create custom sections

toc_object_entries_show_parents = "hide"
