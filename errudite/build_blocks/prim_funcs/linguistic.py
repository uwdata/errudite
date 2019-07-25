import traceback
import functools
from typing import Union, List
from spacy.tokens import Doc, Span, Token
from collections import Counter
from .token import token_pattern
from ...utils.helpers import convert_doc, convert_list
from ...processor.helpers import get_token_feature
from ...utils.check import DSLValueError
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

from ..prim_func import PrimFunc

@PrimFunc.register()
def STRING(target: Union['Target', Span]) -> str:
    """Get the raw string from a given span or target.
    
    Parameters
    ----------
    target : Union[Target, Span]
        The target to be converted to string.
    
    Returns
    -------
    str
        The string.
    """
    output = ""
    try:
        if not target:
            raise DSLValueError(f"No valid input to [ STRING ]. target: {target}")
        else:
            target = convert_list(target)
            doc = convert_doc(target)[0]
            if 'label' in target[0].__class__.__name__.lower():
                output = target[0].get_label()
            elif doc:
                output = doc.text
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ STRING ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        #pass
        return output

@PrimFunc.register()
def LABEL(target: 'Label') -> str:
    """Get the raw string from a label target.
    
    Parameters
    ----------
    target : Label
        The label object (target) to be converted to string.
    
    Returns
    -------
    str
        The string.
    """
    output = ""
    try:
        if not target:
            raise DSLValueError(f"No valid input to [ LABEL ]. target: {target}")
        else:
            target = convert_list(target)
            if 'label' not in target[0].__class__.__name__.lower():
                raise DSLValueError(
                    f"The input to [ LABEL ] needs to be a Label object. target: {target} ({type(target)})")
            else:
                output = target[0].get_label()
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ LABEL ]: {e}")
        raise(ex)
        #logger.error(ex)
    #finally:
    else:
        #pass
        return output

def linguistic(
    spans: Union['Target', Span], 
    label: str='lemma', 
    pattern: Union[str, List[str]]=None,
    get_root: bool=False,
    get_most_common: bool=False) -> Union[str, List[str]]:
    """
    Return the specified linguistic feature of a span with one more more tokens. 
    
    If ``pattern`` is provided, it is used to filter and get the sub-list of spans in the span list.
    For example, if ``pattern=="NOUN"``, then the overlap will only be on tokens with a ``NOUN`` tag.
    
    If ``get_root==True``, gets the single linguistic feature of the *primary* token, 
    or the one within the ground truth span that is highest in the dependency parsing tree.

    *When using the DSL parser*, this function can be called in the following alternative ways, 
    with ``label`` being automatically filled in: ``[LEMMA|POS|TAG|ENT](spans, pattern, get_root)``.
    
    Parameters
    ----------
    spans : Union[Target, Span]
        The span or target to get the info.
    label : str, optional
        The linguistic feature. Could be ``lemma, ent_type, pos``.
    pattern : Union[str, List[str]], optional
        Query the specific pattern, by default None
    get_root : bool, optional
        If to get the single linguistic feature of the *primary* token, by default False
    get_most_common : bool, optional
        If to get the most frequently occurred linguistic feature, by default False
    
    Returns
    -------
    Union[str, List[str]]
        The linguistic feature, or feature list if (1) multiple spans are given, and 
        (2) `get_root` and `get_most_common` are both false.
    """    
    output = ""
    try:
        NOT_INCLUDE_POS = ['ADP', 'IN', 'RP', 'RB', 'DET', 'CONJ', 'PUNCT', 'CCONJ', 'PART', 'SCONJ', 'SYM']
        def linguistic_ent_(span):
            if not span:
                return None
            span = convert_doc(span, strict_format='doc')
            if get_root:
                if type(span) == Doc:
                    span = list(span.sents)[0].root
                elif type(span) == Span:
                    span = span.root
                else:
                    return None
            print(type(span))
            if type(span) == Token:
                if get_token_feature(span, 'ent'):
                    return get_token_feature(span, 'ent')
                else:
                    return None
            ents = [get_token_feature(i, 'ent') for i in span]
            if get_most_common:
                count_arr = []
                for ent in ents:
                    count_arr += len(ent) * [ent]
                c = Counter(count_arr)
                # get the most frequently occurring linguistic feature
                feature, count = c.most_common()[0]
                if count < len(span) * 0.5:
                    return None
                return feature
            else: 
                return ents

        def linguistic_(span):
            if not span:
                return None
            span = convert_doc(span)

            if type(span) == Token:
                return get_token_feature(span, label.lower())
            elif type(span) == Span and len(list(span)) == 1:
                return get_token_feature(list(span)[0], label.lower())
            if get_root:
                if type(span) == Doc:
                    span = list(span.sents)[0].root
                elif type(span) == Span:
                    span = span.root
                else:
                    return None                
            # convert to list            
            if type(span) == Token:
                return get_token_feature(span, label.lower())
            span_list = convert_list(list(span))
            if len(span_list) == 1:
                return get_token_feature(span_list[0], label.lower())
            # if has pattern, filter the span list to only keep things in the selected pattern
            # delete unnecessary tokens from the list if more than one token is highlighted
            filtered_span = [ 
                t for t in span_list if 
                    (t.pos_ not in NOT_INCLUDE_POS and 
                    not t.is_stop and
                    get_token_feature(t, label) != '') or not get_most_common
            ]
            filtered_span = span_list if not filtered_span else filtered_span
            token_features = [get_token_feature(t, label) for t in filtered_span]
            if get_most_common:
                c = Counter(token_features)
                # get the most frequently occurring linguistic feature
                feature, _ = c.most_common()[0]
                return feature
            else: 
                return token_features
        
        # first, transfer span if have pattern.
        spans = token_pattern(spans, pattern=pattern)
        if type(spans) == list:
            if label.startswith('ent'):
                linguistics = [ linguistic_ent_(span) for span in spans ] 
            else:
                linguistics = [ linguistic_(span) for span in spans ]
            linguistics = [l for l in linguistics if l]
            if len(linguistics) == 1:
                output = linguistics[0]
            else:
                output = linguistics # convert_token
        else:
            output = linguistic_ent_(spans) if label.startswith('ent') else linguistic_(spans) # convert_token
    except DSLValueError as e:
        logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ linguistic ({label}) ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        #pass
        return output

for ling in ["lemma", "ent_type", "pos", "tag", "dep", "orth"]:
    PrimFunc.register(ling.upper())(functools.partial(linguistic, label=ling))