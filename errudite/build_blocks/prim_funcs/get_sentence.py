import traceback
import numpy as np
from spacy.tokens import Span
from typing import List, Union
from ...utils.helpers import convert_list
from ...utils.check import DSLValueError

import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
from ..prim_func import PrimFunc

@PrimFunc.register()
def sentence(
    answer: 'QAAnswer', context: 'Context', 
    shift: Union[int, List[int]]=0) -> Span:
    """
    *Machine Comprehension only* Get the sentence that contains a given answer. 
    Shift indicates if neighboring sentences should be included.
    
    Parameters
    ----------
    answer : QAAnswer
        The selected answer.
    context : Context
        The context target of a given instance.
        *Automatically filled in when using the DSL parser.*
    shift : Union[int, List[int]], optional
        Shift indicates if neighboring sentences should be included,  by default 0
        If ``shift==0``, then the actual sentence is returned; 
        if ``shift==[-2,-1,1,2]``, then the four sentences surrounding the answer sentence are returned.
    
    Returns
    -------
    Span
        The selected sentence that contains the answer.
    """
    output = None
    try:
        if not context or context.__class__.__name__ != "Context":
            raise DSLValueError(f"Cannot retrive the sentence, due to invalid context: [ {context} ].")
        if not answer or \
            not ("Answer" in answer.__class__.__name__ or \
            (type(answer) == list and "Answer"  in answer[0].__class__.__name__)):
            raise DSLValueError(f"Cannot retrive the sentence, due to invalid answer: [ {answer} ].")
        # only getting one sentence
        if type(answer) != list and type(shift) != list:
            output = context.get_sentence(answer.sid)
        # multiple sentences. Convert both into list
        answer = convert_list(answer)
        shift = convert_list(shift)
        sids = []
        for a in answer:
            sids += [a.sid + r for r in shift ]
        sids = np.unique(sids)
        output = context.get_sentence(sids)
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ sentence ]: {e}")
        #logger.error(ex)
        raise(ex)
    else:
        #pass
        return output