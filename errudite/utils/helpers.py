from typing import List, Union, Callable
from spacy.tokens import Token, Span, Doc

import re
import inspect 

def func_to_str(func: Callable):
    if callable(func):
        return inspect.getsource(func)
    else:
        return str(func)

def str_to_func(func: str): 
    try:
        p = r"^def (?P<func_name>\w+)\s*\("
        pattern = re.compile(p)
        g = pattern.match(func)
        exec(func, globals())
        return globals().copy()[g['func_name']]
    except:
        return func


def get_token_feature(t: Token, label: str) -> str:
    """Get the linguistic feature given a Spacy.Token obj and a label
    
    Arguments:
        t {Token} -- input token
        label {str} -- linguistic feature to return 
    
    Returns:
        str -- linguistic feature
    """

    if label in ['text', 'orth']:
        return t.text
    if label.lower() == 'ent':
        label = 'ent_type'
    return getattr(t, '{}_'.format(label.lower()), '')

def convert_list(entry: any) -> list:
    # special case: if None, just return
    return [ entry ] if entry != None and type(entry) != list else entry

def convert_str(entry: any) -> str:
    return f'"{entry}"' if type(entry) == str else entry

def merge_list(lists: List[List]) -> list:
    if lists == None:
        return []
    lists = [ l for l in lists if l != None ]
    return sum(lists, [])

def convert_doc(doc: Union[Doc, Span, 'Target'], strict_format: str=None):
    def _strict_doc(doc):
        if not doc:
            return None
        if type(doc) == str:
            return doc
        if strict_format == 'doc':
            return doc if type(doc) == Doc else doc.as_doc()
        if strict_format == 'span':
            return doc if type(doc) == Span else doc[:]
        return doc
    def _convert(doc):
        if type(doc) == str:
            return doc
        if type(doc) == Doc or type(doc) == Span:
            return _strict_doc(doc)
        else:
            return _strict_doc(getattr(doc, 'doc', None))
    if not doc:
        return None
    if type(doc) == list:
        return [ _convert(d) for d in doc ]
    else:
        return _convert(doc)