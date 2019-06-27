from .remove_clue import RemoveClue
from .remove_context_sent import RemoveContextSentence
from .resolve_coref import ResolveCoref

rewrite_list = []

rewrite_list.append(RemoveContextSentence())
rewrite_list.append(ResolveCoref())
rewrite_list.append(RemoveClue())

QA_REWRITES = {e.rid: e for e in rewrite_list}
VQA_REWRITES =  {}
QA_REWRITES = {}