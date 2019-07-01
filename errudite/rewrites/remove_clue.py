# customized replace function with spacy's pattern matching 
from typing import List, Dict
from spacy.tokens import Token

from .rewrite import Rewrite
from ..targets.instance import Instance

@Rewrite.register("RemoveClue")
class RemoveClue (Rewrite):
    """
    A rewrite rule that automatically remove part of the question string:
    It deletes subtrees of the sentence, with the dep being ``dep``.

    .. code-block:: python

        from errudite.rewrites import Rewrite
        Rewrite.by_name("RemoveClue")
    """
    def __init__(self, 
        rid: str='remove_clues',
        description: str='Remove part of the text to reduce the clue.',
        target_cmd: str='question', **kwargs):
        Rewrite.__init__(self, rid, 'auto', description, target_cmd)
    '''
    def match(self, identifier: Identifier, question: Question, paragraph: Paragraph) -> Token:
        matched = None
        sentence = paragraph.get_sentence(identifier.sid)
        q_tokens = list(filter(self.tag_filter, question.doc))
        s_tokens = list(filter(self.tag_filter, sentence.doc))

        q_lemma = [t.lemma_ for t in q_tokens]
        s_lemma = [t.lemma_ for t in s_tokens]
        overlap_token = list(set(q_lemma) & set(s_lemma))
        if overlap_token:
            lemma = overlap_token[0]
            matched = q_tokens[q_lemma.index(lemma)]
        return matched
    '''
    def _rewrite_target(self, instance: Instance) -> str:  # if the editing happened.
        target = self._get_target(instance)
        if not target:
            return None
        for word in target:
            if word.dep_ in ('prep'):
                subtree_span = word.doc[word.left_edge.i : word.right_edge.i + 1]                
                if len(subtree_span) > 1 \
                    and len(subtree_span) < 0.5 * len(target) \
                    and any([w.pos_ == 'NOUN'for w in subtree_span]) \
                    and all([ w.tag_ not in ['WRB', 'WP', 'WDT', 'WP$'] for w in subtree_span]):
                    prev = word.doc[:word.left_edge.i-1] if word.left_edge.i > 0 and word.doc[word.left_edge.i-1].is_punct else word.doc[:word.left_edge.i]
                    nex = word.doc[word.right_edge.i+2:] if word.right_edge.i+2 < len(word.doc) and word.doc[word.right_edge.i+1].is_punct else word.doc[word.right_edge.i+1:]
                    return prev.text + ' ' + nex.text
        return None
