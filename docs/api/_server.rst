Run the Graphical User Interface
================================

The following command runs the visual GUI (note that currently we only
support machine comprehension and visual question answering): 

.. code-block:: bash

    python -m errudite.server

    Commands:
        config_file
                    A yaml config file path.

The config file looks like the following: 

.. code-block:: yml

    task: qa # the task, should be "qa" and "vqa".
    cache_path: {cache_path}/{cache_folder_name}/ # the cached folder.
    model_metas: # a model.
    - name: bidaf
    model_class: bidaf # an implemented model class
    model_path: # a local model file path
    # an online path to an Allennlp model
    model_online_path: https://s3-us-west-2.amazonaws.com/allennlp/models/bidaf-model-2017.09.15-charpad.tar.gz
    description: Pretrained model from Allennlp, for the BiDAF model (QA)
    attr_file_name: null # It set, to load previously saved analysis.
    group_file_name: null
    rewrite_file_name: null
