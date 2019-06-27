import itertools
import functools
import traceback
from typing import Union, List
from spacy.tokens import Span
from ...utils.helpers import convert_list
from ...utils.check import DSLValueError
from ..prim_func import PrimFunc

def answer_offset(
    pred: 'QAAnswer',
    groundtruths: Union['QAAnswer', List['QAAnswer']],
    context: 'Context',
    direction: str='left',
    get: str='delta') -> Union[Span, int]:
    """
    *Machine Comprehension only* Compute the offset between 
    prediction and ground truth in the left or right direction. 
    Depending on ``get``, this function returns either the offset
    spans, or the position differences.

    *When using the DSL parser*, this function can be called in alternative ways, 
    with ``get`` being automatically filled in: 
    ``[answer_offset_delta|answer_offset_span](...)``.
    
    Parameters
    ----------
    pred : QAAnswer
        The selected prediction.
    groundtruths : Union[QAAnswer, List[QAAnswer]]
        The groundtruth(s).
        *Automatically filled in when using the DSL parser.*
    context : Context
        The context object where the ``pred`` and ``groundtruths`` come from.
        *Automatically filled in when using the DSL parser.*
    direction : str, optional
        Compute the delta between the start idx of spans if 'left', or the end
        idx of spans if 'right', by default 'left'.
    get : str, optional
        Determines the output type. If 'delta', return the position differences (``int``). 
        If 'span', return the actual spans, by default 'delta'
    
    Returns
    -------
    Union[Span, int]
        Either the differing spans or the position difference.
    """
    output = None
    try:
        if not groundtruths or not pred or not context:
            raise DSLValueError(f"No valid input to [ answer_offset ]. input: {groundtruths}, {pred}, {context}")
        def no_overlap(a: 'Answer', b: 'Answer'):
            return a.span_end <= b.span_start or b.span_end <= a.span_start
        def offset_(a, b):
            # no overlap between the two answer
            if no_overlap(a, b):
                return (None, None)
            # if no offset on the selected direction
            idx_type = 'span_start' if direction == 'left' else 'span_end'
            idx_a, idx_b = getattr(a, idx_type, -1), getattr(b, idx_type, -1)
            delta = idx_b - idx_a
            if delta == 0:
                span = None
            elif delta > 0:
                span = context.doc[idx_a:idx_b]
            else:
                span = context.doc[idx_b:idx_a]
            return (delta, span)
        answers_a = convert_list(groundtruths)
        answers_b = convert_list(pred)
        offset_list = [offset_(a, b) for a, b in itertools.product(answers_a, answers_b)]
        offset_list = [ o for o in offset_list if o[0] != None]
        # sort based on the absolute offset distance.
        # return the smallest one.
        offset_list = sorted(offset_list, key=lambda x: abs(x[0]))
        if offset_list:
            output = offset_list[0][0] if get == 'delta' else offset_list[0][1]
        else:
            output = None
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ answer_offset ({get}) ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        #pass
        return output

PrimFunc.register('answer_offset_delta')(functools.partial(answer_offset, get='delta'))
PrimFunc.register('answer_offset_span')(functools.partial(answer_offset, get='span'))
