from typing import List, Dict, Callable
from spacy.tokens import Token
import functools

import inspect

from .rewrite import Rewrite
from ..targets.instance import Instance
from ..utils import str_to_func, func_to_str


@Rewrite.register("RewriteCustomFunc")
class RewriteCustomFunc (Rewrite):
    """
    A rewrite class that allows customized rewrite functions.

    This can be queried via:
    
    .. code-block:: python

        from errudite.rewrites import Rewrite
        Rewrite.by_name("RewriteCustomFunc")
        
    Parameters
    ----------
    rewrite_func : Callable[[Instance], str]
        The rewritting function that rewrite the target of the input instance,
        and return the rewritten string.
    target_cmd : str, optional
        The target to be rewritten. It has to be a 
        member of ``Instance.instance_entries``, by default 'question'
    rid : str, optional
        The id/name of the rewrite rule, by default None.
        If not given, use the name of the rewrite func.
    description : str, optional
        The description of the rule, by default 'Customized rewrite function'
    """
    def __init__(self, 
        rewrite_func: Callable[[Instance], str], 
        target_cmd: str,
        rid: str=None,
        description: str='Customized rewrite function', # a brief description
        **kwargs):
        Rewrite.__init__(self, rid, 'auto', description, target_cmd)
        rewrite_func = str_to_func(rewrite_func)
        self._rewrite_target = functools.partial(rewrite_func)
        self._rewrite_func = rewrite_func
        if rid:
            self.rid = rid
        else:
            self.rid = rewrite_func.__name__
    
    def get_json(self):
        """Get the json version definition of the rewrite rule.
        
        Returns
        -------
        Dict[str, str]
            The json version definition of the built block, with:
            rid, category, description, target_cmd and class 
            in a dict.
        """
        return {
            'rid': self.rid,
            'category': self.category, 
            'description': self.description,
            'target_cmd': str(self.target_cmd),
            'rewrite_func': func_to_str(self._rewrite_func),
            'class': self.__class__.__name__
        }