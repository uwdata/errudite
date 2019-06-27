Rewrite Rules
=============

For scalable counterfactual analysis, Errudite uses rules to rewrite all relevant 
instances within a group – similar to search and replace but with the flexibility 
and power of the Errudite DSL.

All the rules are defined under ``errudite.rewrites.rewrite.Rewrite``. This is a 
subclass of `errudite.utils.registrable.Registrable` and all the actual rewrite 
rule classes are registered under ``Rewrite`` by their names.

.. toctree::
   errudite.rewrites

There are three large types of rewrite rules: (1) defaults, (2) those implemented in the 
syntax of ``rewrite(target,from -> to)``, and (3) those that allow customized raw python
functions.

.. toctree::
   errudite.rewrites.defines
   errudite.rewrites.rewrite_custom_func
   errudite.rewrites.defaults
   

