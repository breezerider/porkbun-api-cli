# -*- coding: utf-8 -*-
import os

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.ifconfig',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'sphinx_click',
]
source_suffix = '.rst'
master_doc = 'index'
project = 'porkbun-api-client'
year = '2024'
author = 'Oleksandr Ostrenko'
copyright = '{0}, {1}'.format(year, author)
version = 'develop'
# version = release = '0.1.0'

pygments_style = 'trac'
templates_path = ['.']
extlinks = {
    'issue': ('https://github.com/breezerider/porkbun-api-client/issues/%s', '#'),
    'pr': ('https://github.com/breezerider/porkbun-api-client/pull/%s', 'PR #'),
}
# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only set the theme if we're building docs locally
    html_theme = 'sphinx_rtd_theme'

html_use_smartypants = True
html_last_updated_fmt = '%b %d, %Y'
html_split_index = False
html_sidebars = {
    '**': ['searchbox.html', 'globaltoc.html', 'sourcelink.html'],
}
html_short_title = '%s-%s' % (project, version)

napoleon_google_docstring = False  # Turn off googledoc strings
napoleon_numpy_docstring = True  # Turn on numpydoc strings
napoleon_use_ivar = True  # For maths symbols
napoleon_use_rtype = False  # Inline return type
napoleon_use_param = False  # Single params role
napoleon_use_keyword = False  # Single keywors role
