.. errudite documentation master file, created by
   sphinx-quickstart on Sun Jun 23 23:01:10 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Overview
========

Errudite is an opensourced software tool for performing and sharing error analyses
in natural language processing tasks. Errudite is designed following three principles: 

* First, error groups should be precisely defined for reproducibility; 
  Errudite supports this with an expressive domain- specific language. 
* Second, to avoid spurious conclusions, a large set of instances should be analyzed, 
  including both positive and neg- ative examples; Errudite enables systematic grouping 
  of relevant instances with filtering queries.
* Third, hypotheses about the cause of errors should be explicitly tested; 
  Errudite supports this via automated counterfactual rewriting. 

Abstract Data Classes
---------------------

As the basis for extending Errudite to other tasks and predictors, we use two abstract class to:

* ``register``customized classes or functions via ``Registrable``, so we could add our own code without extensively 
  touching the source folder.
* ``store`` the objects in a hash variable via ``Store``, so all the created instances and analyses can be easily queried
  and used in various functions.

.. toctree::
   :maxdepth: 2
   
   api/_basic_structural_design

Data Structure design
---------------------

Regardless of the task, raw data are transferred into ``Instance`` s, which
in turn are homogeneous collections of ``Target`` s. 
Which Targets they contain depends on the type of data. 
For example, for machine comprehension (or 
datasets like SQAuD), an instance will have ``Question``, 
``Context``, ``Groundtruths``, and ``Predictions``. 

.. toctree::
   :maxdepth: 4

   api/_targets_and_instances

**We provide some preprocessed cache folders downloading**:

.. toctree::
   :maxdepth: 4

   api/_download_preprocess


Main analysis methods
---------------------

At the core of Errudite is an expressive domain-specific language (DSL) for precisely querying 
instances based on linguistic features. Using composable building blocks in DSL, 
Errudite supports forming semantically meaningful groups and rewriting instances to test 
counterfactuals across all available validation data.

.. toctree::
   :maxdepth: 4

   api/_dsl
   api/_attrs_and_groups
   api/_rewrite_rule

Extension
---------

To extend Errudite to your own task and model, you will need to write your own ``DatasetReader``, 
and your own ``Predictor`` wrapper. A ``DatasetReader`` knows how to turn a file containing a 
dataset into a collection  of ``Instance`` s, and how to handle writting the processed instance 
caches to the cache folders. A ``Predictor`` wraps the prediction function of a model, and transfers
the prediction to ``Label`` targets.

.. toctree::
   :maxdepth: 2

   api/_extensible_dataset_reader
   api/_extensible_predictor

Errudite can be used in JupyterLab, or, for machine comprehension and 
visual question comprehension, we have a graphical user interface:

.. toctree::
   :maxdepth: 2

   api/_server

Acknowledgements
----------------
1. The design and implementation of Errudite is inspired by `Allennlp <http://Allennlp.org>`_.
2. We use `SpaCy <https://spacy.io>`_ as the underlying preprocessing.
3. We use `Altair <http://altair-viz.github.io>`_. for visualizing attributes, groups, and rewrites.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
