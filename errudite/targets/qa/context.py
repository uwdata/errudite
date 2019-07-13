"""The context class. ONLY USED FOR QA
"""
from typing import List, Dict, NamedTuple, Union, Any
from spacy.tokens import Span, Doc
from collections import defaultdict
from ...processor import spans_to_json
from ..target import Target

class ContextKey(NamedTuple):
    aid: int
    cid: int
    vid: int=0
    qid: str=None

class Context(Target):
    """
    A batch of Instances. In addition to containing the instances themselves,
    it contains helper functions for converting the data into tensors.

    Parameters
    ----------
    aid : int
        article id.
    cid : int
        context id
    text : str
        The raw text will be processed with SpaCy.
    vid : int, optional
        The version, by default 0. When an instance/a target is rewritten, the version 
        will automatically grow.
    qid : str
        question id, if the context is modified based on a specific question. by default None.
    annotator : SpacyAnnotator, optional
        The annotator, by default None. If None, use the default annotator.
    metas : Dict[str, any], optional
        Additional metas associated with a target, in the format of {key: value}, by default {}
    """

    def __init__(self, 
        aid: int, 
        cid: int, 
        text: str, 
        vid: int = 0, 
        qid: str = None, 
        annotator=None, 
        metas: Dict[str, any]={}) -> None:
        Target.__init__(self, qid, text, vid, annotator=annotator, metas=metas)
        self.aid: int = aid
        self.cid: int = cid

    def key(self) -> ContextKey:
        return ContextKey(aid=self.aid, cid=self.cid, qid=self.qid, vid=self.vid)

    def generate_id(self) -> str:
        return 'aid:{0}-cid:{1}-qid:{2}-vid:{3}'.format(
            self.aid,
            self.cid, 
            self.qid if self.qid else '', 
            self.vid)

    def get_sentence(self, sid: Union[int, List[int]]=0, doc: Doc=None) -> Union[Span, List[Span]]:
        """Query a sentence in a paragraph.
        
        Keyword Arguments:
            sid {Union[int, List[int]]} -- sid the sentence id; or. (default: {None})
        
        Returns:
            Union[Span, List[Span]] -- the sentence
        """
        if doc:
            sentences = list(doc.sents)
        else:
            sentences = list(self.doc.sents)
        if type(sid) == int or type(sid) == float:
            if int(sid) >= 0 and int(sid) < len(sentences):
               return sentences[int(sid)]
        # else if it's an array
        sid = [int(s) for s in sid if s >= 0 and s < len(sentences)]
        if len(sid) > 0:
            filtered = [sentences[s] for s in sid]
            return filtered[0] if len(filtered) == 1 else filtered
        if sentences:
            return sentences[0]
        return None

    @staticmethod
    def get_target(
        candids: Union[List['Context'], Dict[str, 'Context']], 
        aid: int, cid: int, qid: str, vid: int) -> 'Context':
        key = ContextKey(aid=aid, cid=cid)
        if not candids or (type(candids) == dict and not key in candids):
            return None
        if type(candids) == list:
            arr = candids
        else:
            arr = candids[key]
        vids = [vid] if vid == 0 else [vid, 0]
        for v in vids:
            filtered = list(filter(lambda x: x.vid == v and (v == 0 or x.qid == qid), arr))
            if len(filtered) > 0:
                return filtered[0]
        return None

    @staticmethod
    def build_hash_dict(arr: List['Context']) -> Dict[str, 'Context']:
        included_hash = defaultdict(bool)
        a_hash = defaultdict(list)
        for a in arr:
            a_key = a.key()
            if included_hash[a_key]:
                continue
            hash_ = ContextKey(aid=a.aid, cid=a.cid)
            a_hash[hash_].append(a) # append to the actual hash
            included_hash[a_key] = True # save to included hash
        return a_hash

    def serialize(self) -> Dict[str, Any]:
        """Serialize the instance.
        """
        return {
            'key': self.generate_id(),
            'aid': self.aid,
            'cid': self.cid,
            'qid': self.qid,
            'vid': self.vid,
            'doc': spans_to_json(list(self.doc.sents))
        }
