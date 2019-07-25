import pyparsing as pp
import traceback
import itertools
import functools
from typing import Union, List, Dict
from spacy.tokens import Doc, Span, Token

from .length import length
from .pattern_parser_operators import matcher, parse_cmd, CUR_SAVED_RULE
from ...utils.helpers import convert_doc, convert_list, merge_list
from ...utils.check import DSLValueError

import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

from ..prim_func import PrimFunc

def token_pattern(
    docs: Union[Doc, Span, 'Target', List],
    pattern: Union[str, List[str]]) -> bool:
    output = []
    try:
        global CUR_SAVED_RULE
        if not pattern: # special case: just return everything
            output = docs
        else:
            if not docs:
                raise DSLValueError("No given doc to [ token_pattern ].")
            docs = convert_list(convert_doc(docs, strict_format='doc'))
            pattern = convert_list(pattern)
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
            returned_spans = []
            for doc in docs:
                for _, start, end in matcher(doc):
                    returned_spans.append(doc[start:end])
            if len(returned_spans) == 1:
                output = returned_spans[0]
            if not returned_spans:
                pass
                #raise DSLValueError(f"No match found for {pattern} in {docs}.")
            else:
                output = returned_spans
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ token_pattern ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        return output

def token_idxes(
    docs: Union[Doc, Span, 'Target', List],
    idxes: Union[int, List[int]]=None) -> Union[Doc, Span, Token]: 
    # TODO: decide if we want the token to be involved?
    output = []
    try:
        if type(idxes) == float:
            idxes = int(idxes)
        # first, make idxes into a 2 int list
        idxes = [idxes, idxes + 1] if type(idxes) == int else idxes
        if idxes:
            idxes = idxes[:2]
        def token_(ori_doc):
            doc = convert_doc(ori_doc)
            # special case: if no idxes specified, return the whole list
            if idxes == None:
                return doc
            if idxes[0] < 0:
                idxes_ = [ i + len(doc) for i in idxes]
            else:
                idxes_ = idxes
            idx_out_of_range = any([ idx < 0 or idx > len(doc) for idx in idxes_ ])
            # not in the correct range
            # not trying to find surroundings of answer, or do not have context
            if idx_out_of_range: #and (not isinstance(ori_doc, Answer) or not paragraph):    
                # wrong place to look things! But for now, still gives the entire instance.
                return doc
            # in range, just return
            if not idx_out_of_range:
                return doc[idxes_[0]:idxes_[1]]
            return None
        if not docs:
            raise DSLValueError("No input to [ token_idx ].")
        if type(docs) == list:
            output = [ token_(doc) for doc in docs ] # convert_token
            output = [ o for o in output if o ]
        else:
            output = token_(docs) # convert_token
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ token_idx ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        #pass
        return output

@PrimFunc.register()
def token(
    docs: Union[Span, 'Target'],
    idxes: Union[int, List[int]]=None,
    pattern: Union[str, List[str]]=None) -> Union[Span, Token]:
    """
    Get a list of tokens from the target based on idxes (sub-list) and 
    pattern. Note that ``idxes`` runs before ``pattern``. 
    That is, if the idxes exist, the pattern filters the idxed doc tokens.
    
    Parameters
    ----------
    docs : Union[Target, Span]
        The doc to be queried.
    idxes : Union[int, List[int]], optional
        Retrive the sub-list of tokens from docs, with idx(es). By default None
    pattern : Union[str, List[str]], optional
        Used to filter and get the sub-list of spans in the doc span list.
        Pattern allows linguistic annotations and automatically detects queries 
        on POS tags and entity types, in ALL CAPS. For example,
        ``(what, which) NOUN)`` may query all docs that have ``what NOUN`` or 
        ``which NOUN``. If a list, then all the patterns in a list are "OR".
        By default None
    
    Returns
    -------
    Union[Span, Token]
        The queried sub-list.
    """
    output = []
    try:
        if not docs:
            raise DSLValueError("No input to [ token ].")
        docs_ = token_idxes(docs, idxes=idxes)
        if pattern:
            output = token_pattern(docs_, pattern)
        else:
            output = docs_
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ token ]: {e}")
        raise(ex)
        #logger.error(ex)
    #finally:
    else:
        return output

@PrimFunc.register()
def has_pattern(
    docs: Union[Doc, Span, 'Target', List],
    idxes: Union[int, List[int]]=None,
    pattern: Union[str, List[str]]=None) -> bool:
    """
    To determine whether the targeted span contains a certain pattern.
    
    Parameters
    ----------
    docs : Union[Target, Span]
        The doc to be queried.
    idxes : Union[int, List[int]], optional
        Retrive the sub-list of tokens from docs, with idx(es). By default None
    pattern : Union[str, List[str]], optional
        Used to filter and get the sub-list of spans in the doc span list.
        Pattern allows linguistic annotations and automatically detects queries 
        on POS tags and entity types, in ALL CAPS. For example,
        ``(what, which) NOUN)`` may query all docs that have "what NOUN" or 
        "which NOUN". If a list, then all the patterns in a list are "OR".
        By default None
    
    Returns
    -------
    bool
        Whether the span/target has the pattern or not.
    """
    output = False
    try:
        if pattern is None:
            raise DSLValueError(f"[ {pattern} ] is not a valid pattern to [ has_pattern ].")
        else:
            tokens = token(docs, idxes=idxes, pattern=pattern)
            if ( type(docs) == list ):
                output = any([ o and length(o) > 0 for o in tokens ])
            else:
                output = tokens and length(tokens) > 0
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ has_pattern ]: {e}")
        raise(ex)
        #logger.error(ex)
    #finally:
    else:
        return output

def boundary_with (
    docs: Union[Span, 'Target'],
    pattern: Union[str, List[str]], 
    direction: str='start') -> Union[Doc, Span, Token]:
    """
    To determine whether the targeted span contains a certain pattern, at the beginning
    or the end of the doc.

    *When using the DSL parser*, this function can be called in alternative ways, 
    with ``direction`` being automatically filled in: 
    ``[starts_with|ends_with](...)``.
    
    Parameters
    ----------
    docs : Union[Target, Span]
        The doc to be queried.
    pattern : Union[str, List[str]]
        The same as in `has_pattern`.
    direction : str
        Either to test the "start" or the "end" of the doc.
    
    Returns
    -------
    bool
        Whether the span/target starts/ends with the pattern or not.
    """
    output = False
    try:
        if pattern is None:
            raise DSLValueError(f"[ {pattern} ] is not a valid pattern to [ boundary_with ].")
        pattern = convert_list(pattern)
        pattern_arr = merge_list([
            parse_cmd(p).gen_pattern_list() for p in pattern])
        if type(pattern_arr) in [ list, tuple ]:
            while type(pattern_arr[0]) in [ list, tuple ]:
                pattern_arr = pattern_arr[0]
        idx_length = len(pattern_arr)
        if direction == 'start':
            idxes = [ 0, idx_length ]
        else:
            idxes = [ -idx_length-1, 0 ] # to also cover the ednding cmd
        output = has_pattern(docs, idxes=idxes, pattern=pattern)
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ {direction}s_with ]: {e}")
        #logger.error(ex)
        raise(ex)
    else:
        return output

PrimFunc.register("starts_with")(functools.partial(boundary_with, direction='start'))
PrimFunc.register("ends_with")(functools.partial(boundary_with, direction='end'))

