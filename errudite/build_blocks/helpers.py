import sys
sys.path.append('..')
sys.path.append('../..')
import itertools
import argparse
import numpy as np
from typing import Dict, NamedTuple, List, Tuple
from collections import defaultdict
from ..utils.helpers import convert_list, get_token_feature
from ..processor.ling_consts import VBs, WHs, NNs

from ..targets.qa.answer import Answer
#from ..targets.interfaces import PerformMeta

def compute_span_info(
    instance, spans, feature_list: List[str], target, info_idxes, predictor_names):
    if target not in ['question', 'context', 'groundtruths']:
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
        info_idxes[target][pattern] = {model: {} for model in predictor_names}
        info_idxes[target][pattern]['cover'] = defaultdict(dict)
    #
    if target != 'predictions':
        info_idxes[target][pattern]['cover']['total'][instance.key()] = True        
    for model in predictor_names:
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

def compute_entry_info(instance, entries, target: str, info_idxes, predictor_names):
    if target == 'context':
        return info_idxes
    TAG_LISTS = ['ent_type', 'lower', 'pos', 'tag']
    entries = convert_list(entries)
    if target == 'groundtruths':
        entries = entries[:3]
    for entry in entries:
        if isinstance(entry, Answer) and not entry.is_groundtruth:
            target = entry.model
        doc = entry.doc
        for start_idx in range(len(doc)):
            for span_length in range(1, 4):
                if start_idx+span_length > len(doc):
                    continue
                spans = doc[ start_idx : start_idx+span_length ]
                for feature_list in itertools.product(TAG_LISTS, repeat=span_length):
                    info_idxes=compute_span_info(
                        instance, spans, feature_list, target, info_idxes, predictor_names)
    return info_idxes

"""
def stats_of_info(info_idxes, total_size, err_sizes):
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
                model_perform_data[model] = PerformMeta (
                    cover=cover_len / total_size,
                    err_cover=len(model_info) / err_sizes[model] if err_sizes[model] else 0,
                    err_rate=len(model_info)/ cover_len if cover_len else 0
                )
            info_idxes_out[target][pattern] = model_perform_data
    return info_idxes_out
"""
