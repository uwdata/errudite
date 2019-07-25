import itertools
import traceback
from typing import Union, List
from spacy.tokens import Doc, Span, Token
from ...utils.helpers import convert_doc, convert_list
from ...processor.helpers import get_token_feature
from ...utils.check import DSLValueError
from ..prim_func import PrimFunc

@PrimFunc.register()
def overlap(
    doc_a: Union['Target', Span], 
    doc_b: Union['Target', Span], 
    label: str='lemma', 
    return_token_list: bool=False) -> Union[float, List[Token]]:
    """
    A directional overlapping: returns the ratio of tokens in ``doc_a`` that also occur in ``doc_b``
    (``len(doc_a & doc_b) / len(doc_a)``) 
    
    Parameters
    ----------
    doc_a : Union[Target, Span]
        One target/span in the computation.
    doc_b : Union[Target, Span]
        One target/span in the computation.
    label : str, optional
        Determines what linguistic feature both docs to be converted to, to do the overlap computation, 
        by default 'lemma'
    return_token_list : bool, optional
        To return the actual token list if True, or the ratio if faulse, by default False
    
    Returns
    -------
    Union[float, List[Token]]
        Either the ratio, or the actual overlapping token list.
    """
    try:
        if not doc_a and not doc_b:
            return 0
        sents_a = convert_list(convert_doc(doc_a))
        sents_b = convert_list(convert_doc(doc_b))
        def overlap_(sent_a, sent_b):
            if not sent_a or not sent_b:
                return 0
            pos = ['PUNCT', 'DET']
            tags = ['WDT', 'WP', 'WP$', 'WRB', 'BES']
            q_lemmas = set([t.lemma_ for t in sent_a if 
                t.pos_ not in pos and 
                t.tag_ not in tags and 
                not t.is_stop and 
                get_token_feature(t, label)])
            s_lemmas = set([t.lemma_ for t in sent_b if 
                get_token_feature(t, label)])
            text_count = len(list(q_lemmas))
            if return_token_list:
                return list(s_lemmas & q_lemmas)
            else:
                return 1.0 * len(list(s_lemmas & q_lemmas)) / text_count if text_count != 0 else 0
        # compare every pair and get the min.
        return max([overlap_(a, b) for a, b in itertools.product(sents_a, sents_b)])
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ overlap ]: {e}")
        #logger.error(ex)
        raise(ex)