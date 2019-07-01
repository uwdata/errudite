Extensible Predictors
=====================

Many analyses in Errudite rely on real-time models predictions (especially
the rewritings). We implement predictors in a way such that it can be extended to 
customized predictors.

All the predictors are defined under ``errudite.predictors.predictor.Predictor``. 
This is a subclass of ``errudite.utils.registrable.Registrable`` and all the actual
predictor classes are registered under ``Predictor`` by their names. 

We also have an Allennlp predictor wrapper.

.. toctree::
   errudite.predictors.predictor

We have several defaul implementations for several different tasks, and for some 
tasks, we also have some default, supporting predictor impelmentations (especially
those from Allennlp.)

.. toctree::
   :maxdepth: 1
   
   errudite.predictors.qa
   errudite.predictors.vqa
   errudite.predictors.nli
   errudite.predictors.sentiment_analysis

