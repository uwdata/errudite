from spacy.tokens import Token, Doc
from typing import List, Dict, Union, Any
from collections import defaultdict
from ..processor import SpacyAnnotator, spans_to_json, span_to_json, spacy_annotator
from .interfaces import InstanceKey
from ..utils.check import DSLValueError

class Target(object):
    """
    A batch of Instances. In addition to containing the instances themselves,
    it contains helper functions for converting the data into tensors.

    Parameters
    ----------
    qid : str
        The id of the instance.
    text : str
        The raw text will be processed with SpaCy.
    vid : int, optional
        The version, by default 0. When an instance/a target is rewritten, the version 
        will automatically grow.
    annotator : SpacyAnnotator, optional
        The annotator, by default None. If None, use the default annotator.
    metas : Dict[str, any], optional
        Additional metas associated with a target, in the format of {key: value}, by default {}
    """
    def __init__(self, 
        qid: str, 
        text: str, 
        vid: int=0, 
        annotator: SpacyAnnotator=None, 
        metas: Dict[str, any]={}) -> None:
        self.qid: str = qid
        self.vid: int = vid
        # this is a spacy.Doc instance
        if text is not None:
            if not annotator:
                annotator = spacy_annotator
            self.doc: Doc = annotator.model(text)
        else:
            self.doc = None
        self.metas = metas
    
    def get_text(self) -> str:
        """Get the text associated with the target.
        
        Returns
        -------
        str
            The string
        """
        doc = getattr(self, 'doc', None)
        if doc:
            return doc.text
        return ''
    
    def get_meta(self, meta_name: str) -> Any:
        """Get the meta of the target.
        
        Parameters
        ----------
        meta_name : str
            The name of the meta. Has to be a key in `self.metas`
        
        Returns
        -------
        Any
            The meta.
        """
        output = None
        try:
            if self.metas and meta_name in self.metas:
                output = self.metas[meta_name]
            else:
                raise DSLValueError(f"Invalid meta name [ {meta_name} ] to {self}.")
        except DSLValueError as e:
            raise e
        finally:
            return output

    def key(self):
        """Return the key of the target's instance, as a Named Tuple.

        Returns
        -------
        InstanceKey
            The key: ``InstanceKey(qid=self.qid, vid=self.vid)``
        """
        return InstanceKey(qid=self.qid, vid=self.vid)
    
    def generate_id(self) -> str:
        """Get the string key: "qid:{self.qid}-vid:{self.vid}"
        
        Returns
        -------
        str
            The stringed key.
        """
        return f'qid:{self.qid}-vid:{self.vid}'

    def serialize(self) -> Dict[str, Any]:
        """Seralize the instance into a json format, for sending over
        to the frontend.
        
        Returns
        -------
        Dict[str, Any]
            The serialized version.
        """
        output = {}
        for key in self.__dict__:
            if key == 'doc':
                output[key] = span_to_json(self.doc) if self.doc else None
            else:
                output[key] = getattr(self, key, None)
        output['key'] = self.generate_id()
        return output
    
    def to_bytes(self) -> 'Target':
        """Change some entries in the target to bytes, for better cache dumping.
        
        Returns
        -------
        Target
            The byte version of the target.
        """
        if type(self.doc) == Doc:
            self.doc = self.doc.to_bytes(exclude=["tensor"])
        return self
    def from_bytes(self) -> 'Target':
        """Change the byte version of the target to normal version.
        Used for reloading the dump.
        
        Returns
        -------
        Instance
            The normal version of the target.
        """
        if self.doc and type(self.doc) != Doc:
            self.doc = Doc(spacy_annotator.model.vocab).from_bytes(self.doc)
        return self

    def __repr__(self) -> str:
        """Override the print func by displaying the key."""
        return f"""[{self.__class__.__name__}] {[self.key()]}\n""" + \
            f"""{self.doc}"""