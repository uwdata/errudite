# customized replace function with spacy's pattern matching 
from typing import List, Dict
from spacy.tokens import Token

from .rewrite import Rewrite
from ..targets.instance import Instance

@Rewrite.register("RemoveContextSentence")
class RemoveContextSentence (Rewrite):
    """
    Implemented for machine comprehension.
    Delete all the sentences in the paragraph except for the one containing the first groundtruth.

    .. code-block:: python

        from errudite.rewrites import Rewrite
        Rewrite.by_name("RemoveContextSentence")

    """
    def __init__(self, 
        rid: str='keep_correct_sentence', # name the hypothesis
        description: str='Delete all the sentences in the paragraph except for the one containing the first groundtruth.', # a brief description
        target_cmd: str='context', **kwargs):
        Rewrite.__init__(self, rid, 'auto', description, target_cmd)

    def _rewrite_target(self, instance: Instance) -> str: 
        # if the editing happened.
        context = instance.get_entry('context')
        g = instance.get_entry('groundtruth')
        output = context.get_sentence(g.sid)
        if output:
            return context.get_sentence(g.sid).text
        else:
            return None