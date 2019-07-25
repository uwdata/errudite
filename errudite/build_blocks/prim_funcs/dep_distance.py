import itertools
import traceback
import math
import numpy as np
from typing import Union, List
from spacy.tokens import Doc, Span, Token
from spacy.matcher import Matcher # pylint: disable=E0611

from .pattern_parser_operators import matcher, parse_cmd, CUR_SAVED_RULE
from ...utils.helpers import convert_list, merge_list
from ...utils.check import DSLValueError
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

from ..prim_func import PrimFunc

@PrimFunc.register()
def dep_distance(
    target: Union['Answer', List['Answer']],
    question: 'Question',
    context: 'Context',
    pattern: Union[str, List[str]]=None) -> float:
    """
    *Machine Comprehension only* Dependency distance between a key question token 
    and the answer token. The key is computed by finding tokens that do not occur
    frequently in the context and is not far from the given answer. 
    
    Parameters
    ----------
    target : Union[Answer, List[Answer]]
        A selected answer object (Or a list.)
    question : Question
        The question target of a given instance.
        *Automatically filled in when using the DSL parser.*
    context : Context
        The context target of a given instance.
        *Automatically filled in when using the DSL parser.*
    pattern : Union[str, List[str]], optional
        Fixes the keyword linguistic feature., by default None
    
    Returns
    -------
    float
        The distance.
    """
    out_ = 1000
    try:
        global CUR_SAVED_RULE
        if pattern:
            pattern = convert_list(pattern)
                
        def dep_distance_(answer):
            global CUR_SAVED_RULE
            if pattern:
                pattern_key = 'pattern' + '::'.join(pattern)
                if pattern_key != CUR_SAVED_RULE:
                    # define a matcher only when it's not the same rule currently used.
                    patterns = merge_list([
                        parse_cmd(p).gen_pattern_list() for p in pattern])
                    if patterns:
                        if 'matcher' in matcher:
                            matcher.remove('matcher')
                        matcher.add('matcher', None, *patterns)
                        CUR_SAVED_RULE = pattern_key
                # get the matched context token
                matches = matcher(question.doc)
                # get all the question tokens that should be included in the computation.
                q_tokens = []
                for _, start, end in matches:
                    q_tokens += list(question.doc[start:end])
            else:
                # compute an automatic list of question 
                pos = ['PUNCT', 'DET']
                tags = ['WDT', 'WP', 'WP$', 'WRB', 'BES']
                q_tokens = [t for t in question.doc if \
                    t.pos_ not in pos and t.tag_ not in tags and not t.is_stop]
            def compute_distance_per_token (token):
                if token.i >= answer.span_start and token.i < answer.span_end:
                    return 0
                else:
                    return min(
                        abs(token.i - answer.span_start), 
                        abs(token.i - answer.span_end + 1))
            # For each question token, 
            # compute whether if occurs in the context, 
            # and if so, for each occurrence, compute a distance
            distance_per_q_lemma = [[
                {'distance': compute_distance_per_token(t), 'ptoken': t}
            for t in context.doc if t.lemma_ == q_t.lemma_] for q_t in q_tokens]
            # get an idx list for filtered question tokens
            q_lemma_idxes = range(len(q_tokens))
            # sort the distance by 
            # (1) rarety of the question token in the context, 
            # and (2) the closest distancee
            q_lemma_idxes = sorted(q_lemma_idxes, 
                key=lambda idx: (len(distance_per_q_lemma[idx]), 
                min([d['distance'] for d in distance_per_q_lemma[idx]], default=1000)))
            # sort the no occurrence ones, and only keep top 3
            q_lemma_idxes = [idx for idx in q_lemma_idxes if \
                len(distance_per_q_lemma[idx]) > 0][:3]
            # choose the closest in top 3
            if q_lemma_idxes:
                distance_min = math.inf
                qtoken, ptoken = None, None
                for q_lemma_idx in q_lemma_idxes:
                    cur_distance = min([d['distance'] for \
                        d in distance_per_q_lemma[q_lemma_idx]])
                    p_token_idx = np.argmin([d['distance'] for \
                         d in distance_per_q_lemma[q_lemma_idx]])
                    if cur_distance < distance_min:
                        distance_min = cur_distance
                        qtoken = q_tokens[q_lemma_idx]
                        ptoken = distance_per_q_lemma[q_lemma_idx][p_token_idx]['ptoken']
                """
                Indicator('context', context.key, annotations=[
                    Annotation(
                        tidx=ptoken.i, 
                        annotate='word: {0}, dist: {1}'.format(qtoken.lemma_, distance_min) )])
                """
                return distance_min
            return None
        if type(target) == list:
            distances = [ dep_distance_(answer) for answer in target ]
            distances = [ d for d in distances if d ]
            return min(distances) if distances else None # convert_token
        else:
            return dep_distance_(target)
    except DSLValueError as e:
        #logger.error(e)
        raise e
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ dep_distance ]: {e}")
        #logger.error(ex)
        raise(ex)
    else:
        #pass
        return out_