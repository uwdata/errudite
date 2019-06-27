errudite.targets.target.Target
==============================

Targets are primitives which allow users to access inputs and 
outputs at different levels of granularity, such as the ``question (q)``, 
passage ``context (c)``, ``ground truth (g)``, the prediction of a model m 
(denoted by ``prediction(model="m")``), sentence and token. Targets can be composed, 
e.g., ``sentence(g)`` extracts the sentence that contains the ground truth span.

.. automodule:: errudite.targets.target
   :members:
