errudite.targets.label
======================
``Label`` is a special subclass of Target, denoting *groundtruth* and *prediction*. 

.. toctree::
   errudite.targets.label

Because `Label` can be of different types (``int``, predefined class ``str``, 
or span ``str`` extracted from certain targets), we define two subclasses of ``Label``.
* ``SpanLabel``: To handle tasks like QA, where the output label is a sequence span 
  extracted from input (context), and therefore is not a predefined set. These labels are similarly processed by SpaCy to be queryable.
* ``PredefinedLabel``: To handle tasks where the output label are discrete, 
  predefined class types. These outputs will not need any preprocessing.

.. toctree::
   errudite.targets.span_label
   errudite.targets.predefined_label