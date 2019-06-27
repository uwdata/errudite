# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../errudite'))

autodoc_mock_imports = [
  'numpy', 'np', 'matplotlib', 'matplotlib.pyplot', 'plt', 'scipy',
  'scipy.sparse', 'sparse', 'pandas', 'tensorflow', 'tensorflow.contrib.rnn',
  'sparse.csr_matrix', 'numbskull', 'numba', 'numbskull.inference',
  'numbskull.numbskulltypes', 'spacy', 'spacy.cli', 'spacy.deprecated',
  'nltk.stem.porter', 'nltk', 'allennlp', 'pattern', 'dill', 'tqdm', 'overrides',
  'jupyterlab', 'spacy.tokens', 'spacy.matcher', 'nltk.corpus', 'nltk.tree',
  'allennlp.models', 'allennlp.models.archival', 'allennlp.predictors',
  'allennlp.predictors.predictor', 'torch'
]

# -- Project information -----------------------------------------------------

project = 'errudite'
copyright = '2019, Tongshuang Wu'
author = 'Tongshuang Wu'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.linkcode',
    'sphinx.ext.mathjax',
    'sphinx.ext.autosummary',
    'sphinx.ext.coverage',
    'numpydoc'
]

# The master toctree document.
master_doc = 'index'
autodoc_member_order = 'groupwise'
autoclass_content = 'both'

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

import inspect

# make github links resolve
def linkcode_resolve(domain, info):
    """
    Determine the URL corresponding to Python object
    This code is from
    https://github.com/numpy/numpy/blob/master/doc/source/conf.py#L290
    and https://github.com/Lasagne/Lasagne/pull/262
    """
    if domain != 'py':
        return None

    modname = info['module']
    fullname = info['fullname']

    submod = sys.modules.get(modname)
    if submod is None:
        return None

    obj = submod
    for part in fullname.split('.'):
        try:
            obj = getattr(obj, part)
        except:
            return None

    try:
        fn = inspect.getsourcefile(obj)
    except:
        fn = None
    if not fn:
        return None

    try:
        source, lineno = inspect.getsourcelines(obj)
    except:
        lineno = None

    if lineno:
        linespec = "#L%d-L%d" % (lineno, lineno + len(source) - 1)
    else:
        linespec = ""

    filename = info['module'].replace('.', '/')
    return "https://github.com/tongshuangwu/errudite/blob/master/%s.py%s" % (filename, linespec)