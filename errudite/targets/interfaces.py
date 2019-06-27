# define some interfaces.

from typing import Dict, NamedTuple, List, Tuple

# some constant value
UNREWRITTEN_RID = 'unrewritten'

# interface classes
class InstanceKey(NamedTuple):
    qid: str
    vid: int

class LabelKey(NamedTuple):
    qid: str
    vid: int
    model: str
    label: str

class PatternCoverMeta(NamedTuple):
    cover: float
    err_rate: float
    err_cover: float

class RewriteOutputMeta(NamedTuple):
    rid: str
    text: str

class PatternMeta(NamedTuple):
    """The matched pattern that's associated for a [template]

    Arguments:
        before {List[Dict[str, str]]} -- [{ORTH: who}, {ORTH: are}, {ORTH: you}]
        after {List[Dict[str, str]]} -- [{ORTH: who}, {ORTH: are}, {ORTH: you}]
    """
    before: List[Dict[str, str]]
    after: List[Dict[str, str]]

class OpcodeMeta (NamedTuple):
    """Edit sequence

    Arguments:
        op {str} -- Operation string. keep|delete|replace|insert
        fromIdxes {List[int]} -- the corresponding idxes in the original sentence
        toIdxes {List[int]} -- the corresponding idxes in the newly generated sentence
    """
    op: str
    fromIdxes: List[int]
    toIdxes: List[int]


class MatchedTokenMeta (NamedTuple):
    """Find the matched ops, and matched tokens in the matched ops. For computing the editing type

    Arguments:
        ops_idxes {Tuple[int, int]} -- (from, to); this is op idx, not in the original sentence.
        tokens_idxes {Tuple[int, int]} -- (from, to);
            this is the token idx in the from_op and to_op.
    """
    # (from, to); this is the idx in the ops, not in the original sentence.
    ops_idxes: Tuple[int, int]
    # this index is the token index in the matched span,
    # not the global sentence index
    tokens_idxes: List[Tuple[int, int]]


class RewriteTypeMeta (NamedTuple):
    """The editing type setting for computing patterns

    Arguments:
        name {str} -- The name of the editing type. See the dict in CONSTANT
        allow_product {bool} -- Allow combinations of different labels
        score {int} -- The info-editing score
        labels {List[str]} -- The linguistic feature labels that can be used here
    """

    name: str
    allow_product: bool
    score: int
    labels: List[str]

class TextPairMeta(NamedTuple):
    """Matched query pair, with texts

    Arguments:
        atext {str} -- the text of query a
        btext {str} -- the text of query b
    """
    atext: str
    btext: str