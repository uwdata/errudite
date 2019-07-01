import math
import os
import traceback
from typing import Union,List
from spacy.tokens import Doc, Span, Token
from ...utils.helpers import convert_doc
from ...utils.check import DSLValueError
from ...targets.instance import Instance

import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

train_token_freq = None
from ..prim_func import PrimFunc

@PrimFunc.register()
def freq(
    target: Union['Target', Span], 
    target_type: str) -> float:
    """
    Returns the frequency of a token occurring in
    the training data, given a target type
    
    Parameters
    ----------
    target : Union[Target, Span]
        The targeted token.
    target_type : str, optional
        Needs to be a key in ``Instance.train_freq`` to 
        help determine the frequency dictionary.
    
    Returns
    -------
    float
        [description]
    """
    output = 0
    try:
        if not Instance.train_freq:
            raise DSLValueError(f"No training data freq.")
        if target_type not in Instance.train_freq:
            raise DSLValueError(f"No training data frequency for {target_type}.")
        def freq_(doc):
            doc = convert_doc(doc)
            spans = list(doc)
            weight = float("inf")
            for span in spans:
                if type(span) == Token:
                    tokens = [ span ]if not (span.is_punct or span.text == '\n') else []
                else:
                    tokens = [token for token in span if not (token.is_punct or token.text == '\n')]
                if not tokens:
                    continue
                weights = [0 if \
                    t.lemma_ not in Instance.train_freq[target_type] else \
                    Instance.train_freq[target_type][t.lemma_] for t in tokens]
                local_min_weight = min(weights)
                weight = local_min_weight if local_min_weight < weight else weight
            if math.isinf(weight):
                return 0
            return weight
        if not target:
            raise DSLValueError(f"Unknown target for training frequency query in [ freq ]: {target}")
        if type(target) == list:
            return min([ freq_(doc) for doc in target ]) # convert_token
        else:
            return freq_(target) # convert_token
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ perform ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        #pass
        return output