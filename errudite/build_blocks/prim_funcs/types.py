import traceback
from typing import Union, List
from collections import Counter
from ...utils.helpers import convert_list
from ...utils.check import DSLValueError
from ..prim_func import PrimFunc

@PrimFunc.register()
def question_type(target: 'Question') -> str:
    """
    *Machine Comprehension only* Returns the question type: either the 
    WH-word or the first word in a sentence.
    
    Parameters
    ----------
    target : Question
        A question target.
    
    Returns
    -------
    str
        The question type.
    """
    try:
        return target.question_type
    except:
        #print(f'[question_type]')
        #traceback.print_exc()
        raise(DSLValueError(f"{type(target)} does not have [ question type ]. Target: {target}"))

@PrimFunc.register()
def answer_type(target: 'Answer') -> str:
    """
    *Machine Comprehension only* Returns the answer type, computed based on 
    TREC (Li and Roth, 2002) and the named entities of the answer. Returns 
    one of the following: ABBR, DESC, ENTY, HUM, LOC, NUM.
    
    Parameters
    ----------
    target : Answer
        An answer target
        
    
    Returns
    -------
    str
        The answer type.
    """
    try:
        answers = convert_list(target)
        answer_types = []
        if not target:
            raise(DSLValueError(f"Not a valid input to [ answer type ]. Target: {target}"))
        for a in answers:
            if a.__class__.__name__ == 'VQAAnswer':
                answer_types += [ a.answer_type ] * a.count
            elif 'Answer' in a.__class__.__name__:
                answer_types.append(a.answer_type)
            else:
                raise(DSLValueError(f"{type(a)} does not have [ answer_type ]. Target: {target}"))
        answer_type, _ = Counter(answer_types).most_common()[0]
        return answer_type
    except DSLValueError as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise Exception(f"Unknown exception from [ answer_type ]: {e}")