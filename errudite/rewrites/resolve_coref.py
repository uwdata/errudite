from typing import List, Dict
from spacy.tokens import Token


from .rewrite import Rewrite
from ..targets.instance import Instance

from ..processor import spacy_annotator
from ..processor.helpers import normalize_text
#from backend.utils.helpers import convert_list
#from backend.build_block.prim_funcs.overlap import overlap

@Rewrite.register("ResolveCoref")
class ResolveCoref (Rewrite):
    """
    The rewrite rule that automatically resolve the coreferences in sentences.
    Needs to use `neuralcoref <https://github.com/huggingface/neuralcoref>`_.

    .. code-block:: python

        from errudite.rewrites import Rewrite
        Rewrite.by_name("ResolveCoref")
    """
    def __init__(self, 
        rid: str='resolve_coref', # name the hypothesis
        description: str='Resolve the coreference in the groundtruth sentence', # a brief description
        target_cmd: str='context', **kwargs):
        Rewrite.__init__(self, rid, 'auto', description, target_cmd)

    def _rewrite_target(self, instance: Instance) -> str: 
        # if the rewriteing happened.
        context = instance.get_entry('context')
        question = instance.get_entry('question')
        qdoc = question.doc.text.lower()
        c_with_coref_info = spacy_annotator.process_text(context.doc.text)
        g = instance.get_entry('groundtruth')
        s = context.get_sentence(g.sid)
    
        def cluster_mention_in_sentence(c, start, end):
            mentions = [ m for m in c.mentions if m.start >= start and m.end <= end ]
            mentions = [ m for m in mentions if \
                        normalize_text(m._.coref_cluster.main.text) not in normalize_text(m.text) and
                        normalize_text(m.text) not in normalize_text(m._.coref_cluster.main.text) ]
            return mentions
        clusters = c_with_coref_info._.coref_clusters if c_with_coref_info._.coref_clusters else []
        clusters = list(filter(lambda c: \
                          normalize_text(c.main.text) in qdoc and \
                          not normalize_text(c.main.text) in s.text.lower() and \
                          cluster_mention_in_sentence(c, s.start, s.end ), 
                          clusters))
        if not clusters:
            return None
        rewritten_doc = spacy_annotator.process_text(c_with_coref_info._.coref_resolved)
        if len(list(rewritten_doc.sents)) != len(list(context.doc.sents)):
            return None    
        rewritten_sentence = context.get_sentence(g.sid, rewritten_doc)
        return ' '.join([context.doc[:s.start].text, rewritten_sentence.text, context.doc[s.end:].text])        

