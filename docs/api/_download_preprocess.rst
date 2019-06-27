Download Precomputed Cache Folders
==================================

If you would like to try out Errudite without doing the preprocessing your own,
Errudite has several precomputed cache folders that can be easily downloaded
and used:


.. code-block:: bash

    python -m errudite.download

    Commands:
        cache_folder_name
                    A folder name. Currently, we allow downloading the following:
                    squad-100, squad-10570.
        cache_path  A local path where you want to save the cache folder to.

After the downloading, the data will be in ``{cache_path}/{cache_folder_name}/``.
The cache folder is in the following structure:

.. code-block:: bash
    .
    ├── analysis # saved attr, group and rewrite json that can be reloaded. 
    │   ├── save_attr.json
    │   ├── save_group.json
    │   └── save_rewrite.json
    ├── evaluations # predictions saved by the different models, with the model name being the folder name.
    │   └── bidaf.pkl
    ├── instances.pkl # Save all the `Instance`, with the processed Target.
    │   # A dict saving the relationship between linguistic features and model performances. 
    │   # It's used for the programming by demonstration.
    ├── ling_perform_dict.pkl
    ├── train_freq.json # The training vocabulary frequency
    └── vocab.pkl # The SpaCy vocab information.