#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# miros documentation sphinx build configuration file
#
# This file only contains a selection of the most common options.
# For a full list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath('../../'))


# -- Project information -----------------------------------------------------

project = 'miros'
copyright = 'Scott Volk'
author = 'Scott Volk'
github_repo = 'https://github.com/aleph2c/miros'
copyright_link = 'https://github.com/aleph2c'

# The major project version
version = '2.0'

# The full version, including alpha/beta/rc tags
release = '2.0'


# -- General configuration ---------------------------------------------------

# needs_sphinx = '2.4.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames. You can specify multiple suffix as a
# list of strings: source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The document name of the “master” document, that is, the document that
# contains the root toctree directive. Default is 'index'.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# A string of reStructuredText that will be included at the end of every
# source file that is read. This is a possible place to add substitutions
# that should be available in every file.
rst_epilog = '''
.. |13ds| replace:: 13 Down Software Inc
'''

# A string of reStructuredText that will be included at the beginning of
# every source file that is read. This is a possible place to add
# substitutions that should be available in every file.
# rst_prolog = """
# .. |13ds| image:: logo.png
# """

# The default language to highlight source code in. The default is 'default'
# which is mostly a superset of 'python' but it fallbacks to 'none' without
# warning if failed. If specfified, the value should be a valid Pygments
# lexer name: https://pygments.org/docs/lexers/
highlight_language = 'default'

# The style name to use for Pygments highlighting of source code.
# If not set, either the theme’s default style or 'sphinx' is selected.
# A good dark style is 'paraiso-dark', 'native' or 'monokai'.
# A good light style is 'paraiso-light', 'autumn' or 'murphy'.
pygments_style = 'paraiso-dark'


# -- Internationalization ----------------------------------------------------

# The code for the language the docs are written in. Any text automatically
# generated by Sphinx will be in that language.
language = 'en'


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages. See the documentation for
# a list of builtin themes.
html_theme = '13ds_theme_one'

# A dictionary of options that influence the look and feel of the selected
# theme. These are theme-specific. See the theme's theme.conf
# Theme values can be accessed in the jinja template as theme_option,
# For example: {{ theme_navbar_logo }}
# https://sphinx.readthedocs.io/en/latest/usage/theming.html#builtin-themes
html_theme_options = {
  'nosidebar': False,
  'navbar_logo': False,
  'docs_start': 'installation'
  }

# A list of paths that contain custom themes, either as subdirectories or as
# zip files. Relative paths are relative to the configuration directory
html_theme_path = ['_themes']

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# The style sheet to use for HTML pages. The filename must be relative to the
# html_static_path. Default is the stylesheet given by the selected theme.
# Setting a stylsheet here will replace any existing stylesheets, unlike the
# html_css_files which adds to existing theme stylesheets.
# html_style = 'example.css'

# A list of CSS files. The entry must be a filename string or a tuple
# containing the filename string and the attributes dictionary. The filename
# must be relative to the html_static_path, or a full URI.
html_css_files = ['css/miros_docs.css']

# A list of JavaScript files. The entry must be a filename string or a tuple
# containing the filename string and the attributes dictionary. The filename
# must be relative to the html_static_path, or a full URI.
# html_js_files = ['js/example.js',
#                  ('js/example.js', {'defer': 'defer'})]

# The “title” for HTML documentation generated with Sphinx’s own templates.
# This is appended to the <title> tag of individual pages, and used in the
# navigation bar as the “topmost” element. It defaults to
# '<project> v<revision> documentation'.
html_title = 'miros documentation'

# A shorter “title” for the HTML docs. This is used for links in the
# header and in the HTML Help docs. If not given, it defaults to html_title.
html_short_title = 'miros'

# If given, this must be the name of an image file (path relative to the
# configuration directory). It is placed at the top of the sidebar.
html_logo = '_static/miros_logo.svg'

# Favicon file (path relative to the configuration directory). It should be a
# Windows-style icon file (.ico), 32x32 pixels.
html_favicon = '_static/favicon.ico'

# Sphinx adds permalinks for each heading. This value determines the text for
# the permalink (it defaults to "¶") and is visible on hover.
html_add_permalinks = '#'

# Builtin sidebar templates that can be rendered are:
#
# localtoc.html   – a fine-grained table of contents (local pages only)
# globaltoc.html  – a coarse-grained toc for the whole doc set, collapsed
# relations.html  – links to the previous and next documents
# sourcelink.html – a link to the source of the current document,
#                   if enabled in html_show_sourcelink
# searchbox.html  – the “quick search” box
#
# In addition to these you can create your own and save to 'templates'.
# Style rules: sidebar content must be wrapped in one of the following:
# <ul>, <h2 class="sidebar-heading"> or other with class="sidebar-content"
# See sidebar_example.html
#
# html_sidebars can be defined for different pages like:
# html_sidebars = {'index': ['globaltoc.html',], '**': ['localtoc.html',]}
html_sidebars = {
   '**': [
     'sidebarlogo.html',
     # 'localtoc.html',
     'globaltoc.html',
     # 'relations.html',
     'sidebarintro.html',
     # 'sourcelink.html',
     # 'sidebar_example.html',
     'searchbox.html'
     ]
}

# The URL which points to the root of the HTML documentation. It is used to
# indicate the location of document like canonical_url.
# html_baseurl = 'http://miros.ca'

# A dictionary of values to pass into the template engine’s context for all
# pages. ie These values can be referenced like {{ github_url }}
html_context = {
  'github_url': github_repo,
  'copyright_link': copyright_link
}

# If true, the reST sources are included in the HTML build as _sources/name.
html_copy_source = False

# If true (and html_copy_source is true as well), links to the reST sources
# will be added to the sidebar.
html_show_sourcelink = False

# If true, “(C) Copyright …” is shown in the HTML footer.
html_show_copyright = True

# If true, “Created using Sphinx” is shown in the HTML footer. Note may or may
# not work depending on the theme.
html_show_sphinx = True

# If this is not None, a ‘Last updated on:’ timestamp is inserted at every
# page bottom, using the given strftime() format. The empty string is
# equivalent to '%b %d, %Y' (or a locale-dependent equivalent.
html_last_updated_fmt = '%b %d, %Y %-I:%M %p'


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'mirosdoc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples:
# (source start file, target name, title, author,
# documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'miros.tex', 'miros Documentation', 'Scott Volk', 'manual'),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples:
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'miros', 'miros Documentation', [author], 1),
]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples:
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc,
     'miros',
     'miros Documentation',
     author,
     'miros',
     'One line description of project.',
     'Miscellaneous'),
]