from typing import Iterable, Iterator, Callable, List, Tuple, Dict, Union
import os
import glob
import itertools
from spacy.tokens import Span
import numpy as np
from collections import Counter, defaultdict
from tqdm import tqdm
from ..utils import Registrable, convert_list, ConfigurationError, \
    load_json, dump_json, dump_caches, load_caches, CACHE_FOLDERS, set_cache_folder
from ..targets.instance import Instance
from ..processor import spacy_annotator, SpacyAnnotator, get_token_feature, VBs, WHs, NNs
from ..targets.label import Label
from ..targets.interfaces import PatternCoverMeta

import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

class DatasetReader(Registrable):
    """
    Adjusted from https://allenai.github.io/allennlp-docs/api/allennlp.data.dataset_readers.html
    A ``DatasetReader`` knows how to turn a file containing a dataset into a collection
    of ``Instance`` s. 
    
    It also handles writting the processed instance caches to the cache folders.
    When fully processed, the cache folder contains several folders/files:
    
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
        
    To implement your own, just override the `self._read` method to return a list of the instances.
    This is a subclass of `errudite.utils.registrable.Registrable` and all the actual rewrite 
    rule classes are registered under ``Rewrite`` by their names.

    Parameters
    ----------
    cache_folder_path : str, optional
        Set the cache folder path, by default None. If not given, the default is ``./caches/``.
        
    """
    def __init__(self, cache_folder_path: str=None):
        if cache_folder_path: 
            set_cache_folder(cache_folder_path)
        else:
            set_cache_folder(CACHE_FOLDERS["cache"])

    def read(self, file_path: str, lazy: bool=False, sample_size: int=None) -> List[Instance]:
        """
        Returns a list containing all the instances in the specified dataset.

        Parameters
        ----------
        file_path : str
            The path of the input data file.
        lazy : bool, optional
            If ``lazy==True``, only run the tokenization, does not compute the linguistic
            features like POS, NER. By default False
        sample_size : int, optional
            If sample size is set, only load this many of instances, by default None
        
        Returns
        -------
        List[Instance]
            The instance list.
        """
        logger.info("Reading instances from lines in file at: %s", file_path)
        instances = self._read(file_path, lazy, sample_size)

        # Then some validation.
        if not isinstance(instances, list):
            instances = [instance for instance in tqdm(instances)]
        if not instances:
            raise ConfigurationError("No instances were read from the given filepath {}. "
                                    "Is the path correct?".format(file_path))
        return instances

    def _read(self, file_path: str, lazy: bool, sample_size: int) -> List[Instance]:
        """
        Reads the instances from the given file_path and returns them as a ``List``.

        Raises
        ------
        NotImplementedError
           Should be implemented in subclasses.
        """
        raise NotImplementedError
        
    def count_vocab_freq(self, file_path: str) -> None:
        """
        Compute the vocabulary from a given data file. This is for getting 
        the training frequency and save to ``Instance.train_freq``. 
        This function calls ``self._read`` with ``lazy=False``.
        
        Parameters
        ----------
        file_path : str
            The path of the input data file. We suggest using the training file!
        
        Returns
        -------
        None
        """
        spacy_annotator_quick = SpacyAnnotator(disable=['parser', 'ner', 'textcat'])
        spacy_annotator_quick.model.max_length = 100000000
        logger.info("Computing vocab frequency from file at: %s", file_path)
        def _count_str_freq(str_arr: List[str]) -> Dict[str, int]:
            token_count = Counter()
            for str_ in tqdm(str_arr):
                total_doc = spacy_annotator_quick.process_text(str_)
                total = [token.lemma_ for token in total_doc if not (token.is_punct or token.text == '\n')]
                token_count += Counter(total)
            return token_count
        target_dicts = self._read(file_path, lazy=True, sample_size=None)
        for key, val in target_dicts.items():
            logger.info(f"Computing {key} frequency.")
            Instance.train_freq[f'{key}_vocab'] = _count_str_freq(val)

    def _text_to_instance(self, *inputs) -> Instance:
        raise NotImplementedError
    
    def create_instance(self, 
        qid: str, additional_keys: Dict[str, Union[str, int]]={}, **targets) -> Instance:
        """Create an instance given the qid, additional keys, and targets and kwargs.
        
        Parameters
        ----------
        qid : str
            The id of the instance.
        additional_keys : Dict[str, Union[str, int]], optional
            Additional keys that can help locate an instance, in the format of {key_name: key}, by default {}
        targets : 
            A list of targets given in the format of target_name=target: Target.

        Returns
        -------
        Instance
            An instance
        """
        instance = Instance(qid=qid, vid=0, additional_keys=additional_keys)
        instance.set_entries(**targets)
        return instance

    def dump(self, 
        instances: List[Tuple['Instance', 'Target']], 
        name: str="instances", 
        folder: str=None) -> str:
        if not folder:
            folder = CACHE_FOLDERS["cache"]
        if not name.endswith(".pkl"):
            name += '.pkl'
        dump_caches(
            obj=[i.to_bytes() for i in instances],
            cache_filepath=os.path.join(folder, name))
        dump_caches(
            obj=spacy_annotator.model.vocab.to_bytes(), 
            cache_filepath=os.path.join(CACHE_FOLDERS["cache"], 'vocab.pkl'))
        instances = [ i.from_bytes() for i in instances ]
        logger.info(f"Dumped {len(instances)} objects to {os.path.join(folder, name)}.")

    def load(self, filename: str="instances", folder: str=None) -> Instance:
        # pylint: disable=no-self-use
        if not folder:
            folder = CACHE_FOLDERS["cache"]
        if not filename.endswith(".pkl"):
            filename += '.pkl'
        loaded_vocab = load_caches(os.path.join(CACHE_FOLDERS["cache"], 'vocab.pkl'))
        if loaded_vocab is not None:
            spacy_annotator.model.vocab.from_bytes(loaded_vocab)
        loaded_instances = load_caches(os.path.join(folder, filename))
        loaded_instances = [ i.from_bytes() for i in loaded_instances ]
        if loaded_instances and isinstance(loaded_instances[0], Instance):
            Instance.set_entry_keys(getattr(loaded_instances[0], "entries", []))
        logger.info(f"Loaded {len(loaded_instances)} objects to {os.path.join(folder, filename)}.")
        return loaded_instances
    
    def dump_preprocessed(self) -> None:
        """
        Save all the preprocessed information to the cache file. It includes 
        ``instances.pkl``, ``ling_perform_dict.pkl``, ``vocab.pkl``, 
        and all the ``evaluations/[predictor_name].pkl``.
        
        Returns
        -------
        None
            [description]
        """
        instances = list(Instance.instance_hash.values())
        predictions = defaultdict(list)
        for i in instances:
            for p in i.get_entry("predictions"):
                predictions[p.model].append(p)
            i.predictions = []
        self.dump(instances)
        for pname, preds in predictions.items():
            self.dump(preds, pname, CACHE_FOLDERS["evaluations"])
        dump_json(Instance.train_freq, os.path.join(CACHE_FOLDERS["cache"], 'train_freq.json'), is_compact=False)
        dump_caches(Instance.ling_perform_dict, os.path.join(CACHE_FOLDERS["cache"], 'ling_perform_dict.pkl'))
        logger.info("Dumped the linginguistic perform dict.")
        

    def load_preprocessed(self, selected_predictors: List[str]=None) -> None:
        """
        Re-store all the preprocessed information. In specific, it reloads:

        * Instances
        * Set the predictions from models as entries of the instances, and set 
          ``Instance.instance_hash``, ``Instance.instance_hash_rewritten``, and ``Instance.qid_hash``.
        * Get the ``Instance.ling_perform_dict``, which saves the relationship between linguistic features 
          and model performances, and ``Instance.train_freq``, which saves the training vocabulary frequency.
        
        Parameters
        ----------
        selected_predictors : List[str], optional
            If set, only load the predictions from the selected predictors. 
            Otherwise, load all the predictors in `cache_path/evaluations`.
            By default None
        
        Returns
        -------
        None
        """

        instances = self.load()
        predictions = {}
        for file in glob.glob(os.path.join(CACHE_FOLDERS["evaluations"], "*.pkl")):
            file = os.path.basename(file)
            model = file.split(".")[0]
            if selected_predictors and model not in selected_predictors:
                continue
            predictions[model] = self.load(file, CACHE_FOLDERS["evaluations"])
            Instance.set_default_model(model)
        for idx, instance in enumerate(instances):
            instance.set_entries(predictions=[ model_preds[idx] for model_preds in predictions.values() ])
        Instance.build_instance_hashes(instances)
        train_freq_file = os.path.join(CACHE_FOLDERS["cache"], 'train_freq.json')
        ling_perform_dict_file = os.path.join(CACHE_FOLDERS["cache"], 'ling_perform_dict.pkl')
        if os.path.isfile(train_freq_file):
            Instance.train_freq = load_json(train_freq_file)
        if os.path.isfile(ling_perform_dict_file):
            Instance.ling_perform_dict = load_caches(ling_perform_dict_file)

    def _compute_span_info(self, 
        instance: Instance, spans: Span, feature_list: List[str], target: str, info_idxes):
        if target not in instance.entries:
            target_name = f'prediction(model="{target}")'
            target = 'predictions'
        else:
            target_name = target
        if len(list(np.unique(feature_list))) > 2:
            return info_idxes
        span_features = [ get_token_feature(t, feature_list[idx]).strip() for idx, t in enumerate(spans) ]
        if any([not s or s in ["(", ")", ","] for s in span_features]):
            return info_idxes
        if any([ f not in VBs +WHs + NNs and feature_list[idx] == 'tag' for idx, f in enumerate(span_features) ]):
            return info_idxes
        pattern = ' '.join(span_features)
        if pattern not in info_idxes[target]:
            info_idxes[target][pattern] = defaultdict(dict)
            info_idxes[target][pattern]['cover'] = defaultdict(dict)
        if target != 'predictions':
            info_idxes[target][pattern]['cover']['total'][instance.key()] = True
        predictions = instance.get_entry('predictions') or []    
        for prediction in predictions:
            model = prediction.model
            if target == 'predictions': 
                if model not in target_name:
                    continue
                else:
                    info_idxes[target][pattern]['cover'][model][instance.key()] = True      
            if instance.is_incorrect(model):
                info_idxes[target][pattern][model][instance.key()] = True
            #print(model, instance.is_incorrect(model))
            #print(info_idxes[target][pattern][model])
        return info_idxes

    def _compute_ling_perform_dict_per_instance(self, instance: Instance, info_idxes: dict):
        if not instance or not isinstance(instance, Instance):
            return info_idxes
        for entry_name in Instance.instance_entries:
            if entry_name == 'context':
                continue
            TAG_LISTS = ['ent_type', 'lower', 'pos', 'tag']
            entries = convert_list(instance.get_entry(entry_name))
            if entry_name == 'groundtruths':
                entries = entries[:3]
            for entry in entries:
                if isinstance(entry, Label) and not entry.is_groundtruth:
                    entry_name = entry.model
                doc =  getattr(entry, 'doc', None)
                if not doc:
                    continue
                for start_idx in range(len(doc)):
                    for span_length in range(1, 4):
                        if start_idx + span_length > len(doc):
                            continue
                        spans = doc[ start_idx : start_idx+span_length ]
                        for feature_list in itertools.product(TAG_LISTS, repeat=span_length):
                            info_idxes=self._compute_span_info(
                                instance, spans, feature_list, entry_name, info_idxes)
        return info_idxes


    def _stats_of_info(self, info_idxes: dict, total_size: int, err_sizes: dict):
        info_idxes_out = {}
        for target, target_info in info_idxes.items():
            info_idxes_out[target] = defaultdict(None)
            for pattern, pattern_info in target_info.items():
                model_perform_data = {}
                for model, model_info in pattern_info.items():
                    if model == 'cover':
                        continue
                    if model in pattern_info['cover'] :
                        cover_len = len(pattern_info['cover'][model])
                    else:
                        cover_len = len(pattern_info['cover']['total'])
                    model_perform_data[model] = PatternCoverMeta (
                        cover=cover_len / total_size,
                        err_cover=len(model_info) / err_sizes[model] if err_sizes[model] else 0,
                        err_rate=len(model_info)/ cover_len if cover_len else 0
                    )
                info_idxes_out[target][pattern] = model_perform_data
        return info_idxes_out

    def compute_ling_perform_dict(self, instances: List[Instance]) -> None:
        """
        Compute the relationship between linguistic features and model performances. 
        It's used for the programming by demonstration. 
        
        Parameters
        ----------
        instances : List[Instance]
            A list of instances.

        Returns
        -------
        None
            The result is saved to ``Instance.ling_perform_dict``. It's in the format of:

            .. code-block:: js
    
                {
                    target_name: {
                        pattern: {
                            model_name: {
                                cover: how many instances are there.
                                err_cover: The ratio of incorrect predictions with the pattern, overall all the incorrect predictions.
                                err_rate: the ratio of incorrect predictions, over all the instances wit the pattern.
                            }
                        }
                    }
                }
        """
        total_size = len(instances)
        info_idxes = defaultdict(lambda : defaultdict(None))
        err_sizes = defaultdict(int)
        # save the errors
        logger.info("Computing linguistic performance distribution per instance...")
        for i in tqdm(instances):
            predictions = i.get_entry("predictions") or []
            for p in predictions:
                if p.is_incorrect():
                   err_sizes[p.model] += 1
            info_idxes = self._compute_ling_perform_dict_per_instance(i, info_idxes)
        logger.info("Computing the final distribution...")
        Instance.ling_perform_dict = self._stats_of_info(info_idxes, total_size, err_sizes)
        #dump_caches(info_idxes_out, CACHE_FOLDERS["cache"] + 'feature_perform_idx.pkl')

