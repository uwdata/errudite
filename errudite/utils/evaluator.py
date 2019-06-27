import sys

from typing import Union, List, Dict, Callable
from collections import Counter, defaultdict

from ..processor.helpers import normalize_text
from ..task_helpers.vqa.evaluator import normalize_answer
from ..utils.check import ConfigurationError
from ..utils.helpers import convert_list

def accuracy_score(prediction: str, ground_truth: str) -> Dict[str, float]:
    """For matching predicted labels and groundtruth labels
    
    Arguments:
        prediction {str} -- prediction string
        ground_truth {str} -- groundtruth string
    
    Returns:
        Dict[str, float] -- A dict with the key being the metric name, the value being the score.
            It can cover multiple scores if needed. 
    """
    return {
        'accuracy': float(prediction == ground_truth)
    }

# QA
def f1_score(prediction: str, ground_truth: str) -> Dict[str, float]:
    """For normalized text span match.
    
    Arguments:
        prediction {str} -- prediction string
        ground_truth {str} -- groundtruth string
    
    Returns:
        Dict[str, float] -- Has single item precision & recall
    """
    if type(prediction) == list:
        prediction_tokens = prediction
    else:
        prediction_tokens = normalize_text(prediction).split()
    if type(ground_truth) == list:
        ground_truth_tokens = prediction
    else:
        ground_truth_tokens = normalize_text(ground_truth).split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return {'f1': 0, 'precision': 0, 'recall': 0}
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return {'f1': f1, 'precision': precision, 'recall': recall}

def exact_match_score(prediction: str, ground_truth: str) -> Dict[str, float]:
    """For normalized text span match.
    
    Arguments:
        prediction {str} -- prediction string
        ground_truth {str} -- groundtruth string
    
    Returns:
        Dict[str, float] -- em being 1.
    """
    return {'em': int(normalize_text(prediction) == normalize_text(ground_truth))}

def metric_max_over_ground_truths(metric_fn: Callable[[str, str], Dict],
    prediction: str, ground_truths: List[str], key: str):
    scores_for_ground_truths = []
    #output = defaultdict(lambda: 0)
    ground_truths = convert_list(ground_truths)
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

def qa_score(prediction: str, ground_truths: List[str]):
    try:
        if prediction is None:
            raise(ConfigurationError("No prediction given to [ qa_score ]"))
        if ground_truths is None:
            raise(ConfigurationError("No groundtruths given to [ qa_score ]"))
        perform = {}
        em_set = metric_max_over_ground_truths(exact_match_score, prediction, ground_truths, 'em')
        f1_set = metric_max_over_ground_truths(f1_score, prediction, ground_truths, 'f1')
        perform['em'] = em_set['em']
        perform['f1'] = f1_set['f1']
        perform['precision'] = f1_set['precision']
        perform['recall'] = f1_set['recall']
        return perform
    except:
        raise

def vqa_accuracy(prediction: str, ground_truths: List[str]) -> Dict[str, float]:
    try:
        if prediction is None:
            raise(ConfigurationError("No prediction given to [ qa_score ]"))
        if ground_truths is None:
            raise(ConfigurationError("No groundtruths given to [ qa_score ]"))
        groundtruths_text = [ normalize_answer(ans) for ans in ground_truths ]
        prediction = normalize_answer(prediction)
        matchs = [ g for g in groundtruths_text if g == prediction ]
        acc = min(1, float(len(matchs))/3)
        return { 'accuracy': acc }
    except:
        raise