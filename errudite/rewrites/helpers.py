from typing import List, Dict
import numpy as np
import sys
"""
from itertools import chain
import nltk
nltk.download('wordnet')
from nltk.corpus import wordnet as wn
"""
from spacy.tokens import Token
from pattern.en import pluralize, singularize, conjugate, referenced # pylint: disable=E0401,E0611
from ..targets.interfaces import OpcodeMeta, RewriteTypeMeta
from ..processor.ling_consts import VBs

REWRITE_TYPES = [
    RewriteTypeMeta(name='unchange', allow_product=False, labels=['lower', 'pos'], score=0), 
    RewriteTypeMeta(name='structural', allow_product=False, labels=['pos'], score=3), 
    RewriteTypeMeta(name='move', allow_product=True, labels=['lower', 'pos'], score=1),
    RewriteTypeMeta(name='change-semantic', allow_product=True, labels=['lower', 'pos'], score=3),
    RewriteTypeMeta(name='change-form', allow_product=True, labels=['tag'], score=2),
    RewriteTypeMeta(name='local-restructure', allow_product=True, labels=['lower', 'pos'], score=4),
    RewriteTypeMeta(name='global-restructure', allow_product=False, labels=['lower'], score=5),
    RewriteTypeMeta(name='large-change', allow_product=False, labels=['lower'], score=5)
]
REWRITE_TYPE_DICT = {e.name: e for e in REWRITE_TYPES}

def match_super(orgin: str, new: str) -> str:
    if orgin[0].isupper():
        new = new[0].upper() + new[1:]
    return new


def get_str_from_pattern(r):
    if 'LOWER' in r:
        return r['LOWER']
    if 'ORTH' in r:
        return r['ORTH']
    return None

# deal with pure form change
def change_matched_token_form(a_token: Token,
    a_pattern: Dict[str, str],
    b_pattern: Dict[str, str]) -> str:
    # first, deal with orth.
    if get_str_from_pattern(b_pattern):
        return get_str_from_pattern(b_pattern)
    elif 'TAG' in b_pattern and 'TAG' in a_pattern:  # deal with the tags
        # singular -> plural
        if a_pattern['TAG'] in ['NN', 'NNP'] and b_pattern['TAG'] in ['NNS', 'NNPS']:
            return pluralize(a_token.text)
        # plural -> singular
        elif b_pattern['TAG'] in ['NN', 'NNP'] and a_pattern['TAG'] in ['NNS', 'NNPS']:
            return singularize(a_token.text)
        # verb form change
        elif a_pattern['TAG'] in VBs and b_pattern['TAG'] in VBs:
            return conjugate(a_token.text, tag=b_pattern['TAG'])
    elif 'POS' in b_pattern and 'POS' in a_pattern:
        # if IS_DEBUGGING == 'change_matched_token_form':
        #    print ('unmachted token form change', a_token, b_token, a_pattern, b_pattern)
        return a_token.text
    return a_token.text



def sequence_matcher(source: List[str], target: List[str], cost=None, merge: bool=True) -> Dict:
    """A self-implemented edited token computation, not really working super correctly.
    
    Arguments:
        source {List[str]} -- source str
        target {List[str]} -- target str
    
    Keyword Arguments:
        cost {[type]} -- Not used at all (default: {None})
        merge {bool} -- if merge consecutive changes (default: {True})
    
    Returns:
        Dict -- {distance: edit distance float, edits: List[OpcodeMeta]}
    """

    # here, source is p, target is q
    '''
    0 for exact matching
    1 for deleting from B to match A
    2 for inserting to B to match A
    3 for substituting to match A
    !!Adjusted from squad analysis code.
    '''
    
    m, n = len(source), len(target)
    distance = np.zeros( (m + 1, n + 1) )
    operation = np.zeros( (m + 1, n + 1) )
    distance[0, :] = np.array(range(n + 1) )
    distance[:, 0] = np.array(range(m + 1) )
    node_delete_op, node_insert_op, node_sub_op = list(), list(), list()
    edits_op = list()
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if cost is None:
                cost_insert = distance[i - 1, j] + 1
                cost_delete = distance[i, j - 1] + 1
                if source[i - 1] == target[j - 1]:
                    cost_sub = distance[i - 1, j - 1]
                else:
                    cost_sub = distance[i - 1, j - 1] + 2
            else:
                cost_insert = distance[i - 1, j] + \
                    cost['insert'].setdefault(source[i - 1], sys.float_info.max / 1000.0)
                cost_delete = distance[i, j - 1] + \
                    cost['delete'].setdefault(target[j - 1], sys.float_info.max / 1000.0)
                if source[i - 1] == target[j - 1]:
                    cost_sub = distance[i - 1, j - 1]
                else:
                    cost_sub = distance[i - 1, j - 1] + \
                    cost['replace'].setdefault( (source[i - 1], target[j - 1] ), sys.float_info.max / 1000.0)

            min_cost = min(cost_insert, cost_delete, cost_sub)
            distance[i, j] = min_cost

            if cost_sub == min_cost and source[i - 1] != target[j - 1]:
                operation[i, j] = 3
            elif cost_insert == min_cost:
                operation[i, j] = 2
            elif cost_delete == min_cost:
                operation[i, j] = 1
    # backtrace
    # note that we have a slightly different version of editing...
    cur_i, cur_j = m, n
    while (cur_i > 0 and cur_j > 0):
        if operation[cur_i, cur_j] == 1:
            edits_op.insert(0, {'etype': 'insert', 'source': cur_i - 1, 'target': cur_j - 1})
            node_delete_op.append( target[cur_j - 1])
            cur_j = cur_j - 1
        elif operation[cur_i, cur_j] == 2:
            edits_op.insert(0, {'etype': 'delete', 'source': cur_i - 1, 'target': cur_j - 1})
            node_insert_op.append(source[cur_i - 1])
            cur_i = cur_i - 1
        else:
            if source[cur_i - 1] != target[cur_j - 1]:
                edits_op.insert(0, {'etype': 'replace', 'source': cur_i - 1, 'target': cur_j - 1})
                node_sub_op.append( (source[cur_i - 1], target[cur_j - 1]))
            else:
                edits_op.insert(0, {'etype': 'equal', 'source': cur_i - 1, 'target': cur_j - 1})
            cur_i -= 1
            cur_j -= 1
    # merge continuously same ones
    revised_ops = []
    op = ''
    
    from_start, from_end, to_start, to_end = 0, 0, 0, 0
    for idx, edit in enumerate(edits_op):
        if not merge or edit['etype'] != op:
            # save the previous one and set the new one
            if op != '':
                revised_ops.append(OpcodeMeta(op=op, fromIdxes=(from_start, from_end), toIdxes=(to_start, to_end)))
            from_start = from_end
            to_start = to_end
        op = edit['etype']
        from_end = edit['source'] + 1 
        to_end = edit['target'] + 1
        if idx == len(edits_op) - 1: # save the last one
            revised_ops.append(OpcodeMeta(op=op, fromIdxes=(from_start, from_end), toIdxes=(to_start, to_end)))
    
    #print(source)
    #print(target)
    #print(edits_op)
    return {'dist': min(distance[m, n], 8), 'edits': revised_ops}
'''
def find_similar_token(word: Token) -> str:
    """Find synonyms from wordnet, given a token's text and POS. If cannot find one, return itself.
    
    Arguments:
        word {Token} -- targeting word
    
    Returns:
        str -- synonym
    """

    if word.lemma_ == 'who':
        return 'whom'
    synonyms = wn.synsets(word.lemma_, getattr(wn, word.pos_, None))
    synonyms = set(chain.from_iterable([[ l.replace('_', ' ').lower() for l in w.lemma_names()] for w in synonyms]))
    if word.lemma_ in synonyms:
        synonyms.remove(word.lemma_)
    if synonyms:
        synonyms = sorted(list(synonyms), key=lambda l: word.similarity(process_text(l)), reverse=True)
        return synonyms[0].lower()
    else:
        return word.text.lower()
'''