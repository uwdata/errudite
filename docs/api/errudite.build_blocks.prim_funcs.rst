Pre-implemented Prim Functions
==============================

Errudite has a list of functions to support computing instance attributes and/or build instance groups. 
These functions are called ``primitive functions`` --- they are *attribute extractors* act on `targets` to extract 
fundamental instance metadata (e.g., `length(q)` returns the length of a question). 
These include:

* basic extractors like length, 
* general purpose linguistic features like token ``LEMMA``, ``POS`` tags, and entity (``ENT``) annotations, 
* standard prediction performance metrics such as ``f1`` or ``accuracy``,
* between-target relations such as ``overlap(t1, t2)``, and 
* domain-specific attributes (e.g., for Machine Comprehension or VQA) such as ``question_type`` and ``answer_type``. 

``prim_funcs`` are composable through standard logical and numerical operators, serving as building blocks 
for more complex attributes.

Converters and targets
----------------------

*Get targets*: These targets contain text spans post-processed with state-of-the-art POS taggers, 
lemmatizers and NER models, along with metadata such as example id, or (in the answer case) 
the model that generated it. When additional metadata is not used, ``Target`` can be treated just as 
``Span`` in a function, or a piece of text with its linguistic features.

.. py:function:: question|context|groundtruth → Target

Automatically query the target object (Question and Answer in VQA and MC, 
as well as Context in Machine comprehension). This can be easily extended to
any key that is in ``Instance.instance_entries``.

.. automodule:: errudite.build_blocks.prim_funcs.get_prediction
   :members:
   :undoc-members:

*Converters* that extract sub-spans, short phrases, or sentences from targets.

.. automodule:: errudite.build_blocks.prim_funcs.token
   :members: token
   :undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.get_sentence
   :members:
   :undoc-members:

General Computation
-------------------

.. automodule:: errudite.build_blocks.prim_funcs.digits
   :members:
   :no-undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.length
   :members:
   :no-undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.freq
   :members:
   :no-undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.get_meta
   :members:
   :no-undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.similar_token
   :members:
   :no-undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.apply
   :members:
   :no-undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.is_rewritten_by
   :members:
   :no-undoc-members:



Linguistic Attributes
---------------------

.. automodule:: errudite.build_blocks.prim_funcs.linguistic
   :members:
   :no-undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.tokenhas_pattern, boundary_with
   :members: 
   :no-undoc-members:



Performance Metrics
-------------------

.. automodule:: errudite.build_blocks.prim_funcs.perform
   :members:
   :no-undoc-members:



Between-target Relations
------------------------

.. automodule:: errudite.build_blocks.prim_funcs.overlap
   :members:
   :no-undoc-members:


Domain-Specific Attributes
--------------------------

.. automodule:: errudite.build_blocks.prim_funcs.dep_distance
   :members:
   :no-undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.logic_operations
   :members:
   :no-undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.offset
   :members:
   :undoc-members:

.. automodule:: errudite.build_blocks.prim_funcs.types
   :members:
   :no-undoc-members: