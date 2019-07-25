import traceback
from typing import Union, List
from spacy.tokens import Doc, Span, Token
from ...utils.helpers import convert_doc
from ...utils.check import DSLValueError
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

from ..prim_func import PrimFunc

@PrimFunc.register()
def length(
    docs: Union['Target', Span, List[Union['Target', Span]]]) -> int:
    """
    The length of a given span, in tokens.
    If the input is a List, take the min length of all spans in the list.
    
    Parameters
    ----------
    docs : Union[Target, Span, List[Union[Target, Span]]]
        The input doc(s) for computing the length.
    
    Returns
    -------
    int
        The length.
    """
    output = 0
    try:
        def length_(doc):
            return len(convert_doc(doc)) if doc else 0
        if docs is None:
            raise DSLValueError(f"No valid input to [ length ]. input: {docs}")
        elif type(docs) == list and len(docs) > 0:
            output = min([ length_(doc) for doc in docs ]) # convert_token
        else:
            output = length_(docs) # convert_token
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ length ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        #pass
        return output