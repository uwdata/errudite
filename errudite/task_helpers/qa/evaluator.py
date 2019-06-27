""" Official evaluation script for v1.1 of the SQuAD dataset. """
from __future__ import print_function
from collections import Counter, defaultdict
import string
import re
import argparse
import json
import sys

from typing import List, Callable, Dict
from ...processor.helpers import normalize_text
'''
Modified: [name] evaluate.v1.1 -> evaulator
'''

def normalize_answer(s: str) -> str:
    """Lower text and remove punctuation, articles and extra whitespace/
    
    Arguments:
        s {str} -- input string
    
    Returns:
        str -- normalized string
    """
    return normalize_text(s)


def f1_score(prediction: str, ground_truth: str) -> Dict[str, float]:
    if type(prediction) == list:
        prediction_tokens = prediction
    else:
        prediction_tokens = normalize_answer(prediction).split()
    if type(ground_truth) == list:
        ground_truth_tokens = prediction
    else:
        ground_truth_tokens = normalize_answer(ground_truth).split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return {'f1': 0, 'precision': 0, 'recall': 0}
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return {'f1': f1, 'precision': precision, 'recall': recall}

def exact_match_score(prediction: str, ground_truth: str) -> Dict[str, float]:
    return {'em': int(normalize_answer(prediction) == normalize_answer(ground_truth))}

def metric_max_over_ground_truths(metric_fn: Callable[[str, str], Dict],
    prediction: str, ground_truths: List[str], key: str):
    scores_for_ground_truths = []
    #output = defaultdict(lambda: 0)
    for ground_truth in ground_truths:
        score = metric_fn(prediction, ground_truth)
        scores_for_ground_truths.append(score)
        """
        for metric, score in score.items():
            if output[metric] < score:
                output[metric] = score
        """
    #return output
    scores_for_ground_truths = sorted(scores_for_ground_truths, key=lambda d: d[key], reverse=True)
    return scores_for_ground_truths[0]

def evaluate(dataset, predictions):
    f1 = exact_match = total = 0
    for article in dataset:
        for paragraph in article['paragraphs']:
            for qa in paragraph['qas']:
                total += 1
                if qa['id'] not in predictions:
                    message = 'Unanswered question ' + qa['id'] + \
                              ' will receive score 0.'
                    print(message, file=sys.stderr)
                    continue
                ground_truths = list(map(lambda x: x['text'], qa['answers']))
                prediction = predictions[qa['id']]
                exact_match += metric_max_over_ground_truths(
                    exact_match_score, prediction, ground_truths, 'em')['em']
                f1 += metric_max_over_ground_truths(
                    f1_score, prediction, ground_truths, 'f1')['f1']

    exact_match = 100.0 * exact_match / total
    f1 = 100.0 * f1 / total

    return {'exact_match': exact_match, 'f1': f1}

if __name__ == '__main__':
    expected_version = '1.1'
    parser = argparse.ArgumentParser(
        description='Evaluation for SQuAD ' + expected_version)
    parser.add_argument('dataset_file', help='Dataset file')
    parser.add_argument('prediction_file', help='Prediction File')
    args = parser.parse_args()
    with open(args.dataset_file) as dataset_file:
        dataset_json = json.load(dataset_file)
        if (dataset_json['version'] != expected_version):
            print('Evaluation expects v-' + expected_version +
                  ', but got dataset with v-' + dataset_json['version'],
                  file=sys.stderr)
        dataset = dataset_json['data']
    with open(args.prediction_file) as prediction_file:
        predictions = json.load(prediction_file)
    print(json.dumps(evaluate(dataset, predictions)))
