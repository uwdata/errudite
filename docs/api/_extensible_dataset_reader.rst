Extensible Dataset Readers
==========================

To extend Errudite to different tasks, We implement the dataset reader in a way such that 
it can be extended to customized dataset handlers.

All the predictors are defined under ``errudite.io.dataset_reader.DatasetReader``. 
This is a subclass of `errudite.utils.registrable.Registrable` and all the actual reader 
classes are registered under ``DatasetReader`` by their names. 

.. toctree::
   errudite.io.dataset_reader

We have several defaul implementations for several different tasks, and for some 
tasks, we also have some default, supporting predictor impelmentations (especially
those from Allennlp.)

.. toctree::
   errudite.io.squad_reader
   errudite.io.snli_reader
   errudite.io.sst_reader

