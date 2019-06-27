import traceback
import os
from typing import List, Dict, Union, Any, Tuple
from collections import defaultdict
from itertools import groupby
from .label import Label
from .target import Target
from .interfaces import InstanceKey, UNREWRITTEN_RID
from ..processor import spacy_annotator
from ..utils.check import ConfigurationError

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

class Instance(object):
    """
    ``Instances`` could be treated as a *wrapper* class of targets, which 
    is used by the DSL to create specific instances. We create instance classes
    by setting the correct entries and keys created by the targets. 
    
    While other entires can flow, **make sure** you set [``predictions`` or ``prediction``] 
    and [``groundtruths`` or ``groundtruth``], depending on how many groundtruths you have, 
    and how many models you are using to predict this one instance.
        
    Parameters
    ----------
    qid : str
        The id of the instance.
    vid : int, optional
        The version, by default 0. When an instance/a target is rewritten, the version 
        will automatically grow.
    rid : str, optional
        The rewrite rule id. If not rewritten (i.e., the original version), it is UNREWRITTEN_RID.
    additional_keys : Dict[str, Union[str, int]], optional
        Additional keys that can help locate an instance, in the format of {key_name: key}, by default {}  
    
    """
    #: ``str``, The selected model. This is what DSL resolve to when we set ``model="ANCHOR"``
    model: str = None 
    #: ``str``, The selected rewrite. This is what DSL resolve to when we set ``rewritten="SELECTED"``
    selected_rewrite: str = UNREWRITTEN_RID 
    #: ``List[str]``, The names of the entry targets saved in the Instance.
    instance_entries: List[str] = []
    #: ``Dict[str, List[InstanceKey]]``, A dict that denotes wraps different versions of instance keys
    qid_hash: Dict[str, List[InstanceKey]] = defaultdict(list)
    #: ``Dict[InstanceKey, Instance]``, A dict that saves all the *original* instances, 
    #: denoted by the corresponding instance keys.
    instance_hash: Dict[InstanceKey, "Instance"] = defaultdict(lambda: None)
    #: ``Dict[InstanceKey, Instance]``, A dict that saves all the *rewritten* instances, 
    #: denoted by the corresponding instance keys.
    instance_hash_rewritten = defaultdict(lambda: None)
    #: ``Dict[str, int]`` The training vocabulary frequency
    train_freq = defaultdict(dict)
    #: ``dict``: The relationship between linguistic features and model performances.
    ling_perform_dict = defaultdict(dict)
    # TODO: save the dev frequency??

    def __init__(self, qid: str, vid: int, rid: str=UNREWRITTEN_RID, 
            additional_keys: Dict[str, Union[str, int]]={}):
        self.qid: str = qid
        self.vid: int = vid
        self.entries: List[str] = []
        self.rid = rid
        self.additional_keys = additional_keys
        for key, val in additional_keys.items():
            setattr(self, key, val)

    def get_all_keys(self) -> Dict[str, Union[int, str]]:
        """
        Get all the instance keys, including the qid, vid, rid, 
        and all the keys in the additional_keys.
        
        Returns
        -------
        Dict[str, Union[int, str]]
            {key_name: key}
        """
        keys = { 'qid': self.qid, 'vid': self.vid, 'rid': self.rid }
        for key, val in self.additional_keys.items():
            keys[key] = val
        return keys
    
    def generate_id(self) -> str:
        """Get the string key: "qid:{self.qid}-vid:{self.vid}"
        
        Returns
        -------
        str
            The stringed key.
        """
        return f"qid:{self.qid}-vid:{self.vid}"

    def key(self) -> InstanceKey:
        """Return the key of the instance as a Named Tuple.

        Returns
        -------
        InstanceKey
            The key: ``InstanceKey(qid=self.qid, vid=self.vid)``
        """
        return InstanceKey(qid=self.qid, vid=self.vid)
    
    def get_perform(self, model: str=None, perform_name: str=None) -> float:
        """
        Get the metric of a given model, based on a performance metric name.
        
        Parameters
        ----------
        model : str, optional
            The selected model, by default ``None``. If ``None``, resolve to ``Instance.model``.
        perform_name : [type], optional
            The queried metric name, by default Label.task_primary_metric
        
        Returns
        -------
        float
            The queried metric. If cannot find the prediction from the model, return 0.
        """
        perform_name = Label.resolve_default_perform_name(perform_name)
        try:
            model = Instance.resolve_default_model(model)
            prediction = self.get_entry('prediction', model)
            if prediction:
                return prediction.get_perform(perform_name)
            else:
                logger.warn(f"Cannot get the prediction from model: [ {model} ]; Returning 0.")
                return 0
        except:
            raise
    
    def is_incorrect(self, model: str=None) -> bool:
        """
        Check if the model has a correct prediction. 
        This function gets the prediction (``Label``) from the model,
        and then call ``prediction.is_incorrect()``.
        
        Parameters
        ----------
        model : str, optional
            The selected model, by default ``None``. If ``None``, resolve to ``Instance.model``.
        
        Returns
        -------
        bool
            If the model is incorrect.
        """
        try:
            prediction = self.get_entry('prediction', model)
            if prediction:
                return prediction.is_incorrect()
            # logger.warn(f"Cannot get the prediction from model: [ {model} ]; Returning False.")
            return False
        except:
            raise

    def set_entries(self, **kwargs) -> None:
        """
        Save the targets as entries of the target, so the instance can 
        serve as the wrapper. It accepts ``**kwargs``, so the names of 
        the targets can be easily customized. It's supposed to be called 
        by ``instance.set_entries(target_name1=target1, target_name2=target2).``
        
        Returns
        -------
        None
            [description]
        """
        Instance.set_entry_keys(list(kwargs.keys()))
        for key, val in kwargs.items():
            if key not in self.entries:
                self.entries.append(key)
            setattr(self, key, val)

    def get_entry(self, entry: str, model: str=None) -> Target:
        """Get a target entry from this instance with the entry name.
        
        Parameters
        ----------
        entry : str
            The name of the target entry.
        model : str, optional
            If the entry is "prediction", an additional model string argument
            can be used to get the specific prediction from a targeted model.
            By default None
        
        Returns
        -------
        Target
            The queried the Target. If non-existing, return ``None``.
        """
        if entry == 'instance':
            return self.key()
        if entry in self.entries:
            output = getattr(self, entry, None)
            return output
        elif entry == 'groundtruth':
            groundtruths = getattr(self, 'groundtruths', [])
            groundtruths = sorted(groundtruths, key=lambda g: getattr(g, 'count', -1), reverse=True)
            return groundtruths[0] if groundtruths else None
        elif entry == 'prediction':
            predictions = getattr(self, 'predictions', [])
            predictions = [ p for p in predictions if p.model == Instance.resolve_default_model(model) ]
            return predictions[0] if predictions else None
        # logger.warn(f"Cannot get the target entry: [ {entry} ] Returning None.")
        return None
    
    def _show_instance_str(self) -> str:
        """
        Generate an instance string that represent the key information of the instance,
        including the keys and the entries.
        
        Returns
        -------
        str
            The instance string.
        """
        output = f"""[{self.__class__.__name__}] [{self.key()}]\n"""
        for entry in self.entries:
            got_entry = self.get_entry(entry)
            if type(got_entry) == list:
                for g in got_entry:
                    if isinstance(g, Label):
                        output += f"[{entry}]\t{g.get_text()}\t{g.model}\t{ g.perform }\n"
                    elif isinstance(g, Target): 
                        output += f"[{entry}]\t{g.get_text()}\n"
                    else: 
                        output += f"[{entry}]\t\n"
            elif isinstance(got_entry, Label):
                output += f"[{entry}]\t{got_entry.get_text()}\t{got_entry.model}\t{got_entry.perform }\n"
            elif isinstance(got_entry, Target):
                output += f"[{entry}]\t{got_entry.get_text()}\n"
            else:
                output += f"[{entry}]\t\n"
        return output
    
    def show_instance(self) -> None:
        """
        Print an instance string that represent the key information of the instance,
        including the keys and the entries.
        
        Returns
        -------
        None
        """
        print(self._show_instance_str())

    def __repr__(self):
        """Override the print func by displaying the key."""
        return f"""{self.__class__.__name__} [{self.key()}]\n"""

    def serialize(self) -> Dict[str, Any]:
        """Seralize the instance into a json format, for sending over
        to the frontend.
        
        Returns
        -------
        Dict[str, Any]
            The serialized version.
        """
        output = {
            'key': self.get_all_keys(),
            'prediction': self.get_entry('prediction').get_text() if self.get_entry('prediction') else '',
            'perform': self.get_perform()
        }
        for entry in self.entries:
            got_entry = self.get_entry(entry)
            if type(got_entry) == list:
                val = [ g.get_text() if isinstance(g, Target) else '' for g in got_entry ]
            elif isinstance(got_entry, Target):
                val = got_entry.get_text()
            else: 
                val = ''
            output[entry] = val
        return output
    
    def to_bytes(self) -> "Instance":
        """Change some entries in the instance to bytes, for better cache dumping.
        
        Returns
        -------
        Instance
            The byte version of the instance.
        """
        for entry in self.entries:
            got_entry = self.get_entry(entry)
            if type(got_entry) == list:
                setattr(self, entry, 
                    [ g.to_bytes() if isinstance(g, Target) else None for g in got_entry ])
            elif isinstance(got_entry, Target):
                setattr(self, entry, got_entry.to_bytes())
        return self

    def from_bytes(self) -> "Instance":
        """Change the byte version of the instance to normal version.
        Used for reloading the dump.
        
        Returns
        -------
        Instance
            The normal version of the instance.
        """
        for entry in self.entries:
            got_entry = self.get_entry(entry)
            if type(got_entry) == list:
                setattr(self, entry, 
                    [ g.from_bytes() if g else g for g in got_entry ])
            elif isinstance(got_entry, Target):
                setattr(self, entry, got_entry.from_bytes())

        return self

    @classmethod
    def set_default_model(cls, model: str) -> None:
        """Set a default model for the whole class instance to share.
        
        Parameters
        ----------
        model : str
            The model name.
        
        Returns
        -------
        None
        """
        cls.model = model

    @classmethod
    def resolve_default_model(cls, model: str=None) -> str:
        """Resolve the actual selected model.
        If ``model`` is given, return model. Otherwise
        (``model=None or model="ANCHOR"``), return ``Instance.model``. 
        
        Parameters
        ----------
        model : str, optional
            The input named model, by default None
        
        Returns
        -------
        str
            The resolved model
        """
        if not model or model == 'ANCHOR':
            return cls.model
        else:
            return model
    
    @classmethod
    def set_default_rewrite(cls, rid: str):
        """Set a default rewrite rule for the whole class instance to share.
        
        Parameters
        ----------
        model : str
            The rewrite rule names.
        
        Returns
        -------
        None
        """
        cls.selected_rewrite = rid
    
    @classmethod
    def resolve_default_rewrite(cls, rid: str=None):
        """Resolve the actual selected rewrite rule.
        If ``rid`` is given, return rid. Otherwise
        (``rid=None or rid="SELECTED"``), return ``Instance.selected_rewrite``. 
        
        Parameters
        ----------
        rid : str, optional
            The input named rewrite rule string, by default None
        
        Returns
        -------
        str
            The resolved model
        """
        if not rid or rid == 'SELECTED':
            return cls.selected_rewrite
        else:
            return rid

    @classmethod
    def get(cls,
        key: InstanceKey, 
        instance_hash: Dict[InstanceKey, 'Instance']={},
        instance_hash_rewritten: Dict[InstanceKey, 'Instance']={}) -> 'Instance':
        """Get the instance by querying its key.

        Parameters
        ----------
        key : InstanceKey
            The key of the intended instance.
        instance_hash : Dict[InstanceKey, Instance]
            A dict that saves all the *original* instances, by default None. 
            It denotes by the corresponding instance keys.
            If ``None``, resolve to ``Instance.instance_hash``.
        instance_hash_rewritten : Dict[InstanceKey, Instance]
            A dict that saves all the *rewritten* instances, by default None. 
            It denotes by the corresponding instance keys.
            If ``None``, resolve to ``Instance.instance_hash_rewritten``.

        Returns
        -------
        Instance
            The queried instance.
        """
        try:
            instance_hash = instance_hash or cls.instance_hash
            instance_hash_rewritten = instance_hash_rewritten or cls.instance_hash_rewritten
            if not key:
                raise(ConfigurationError(f"get_instance_by_key: key cannot be {key} ({type(key)})."))
            if key.vid == 0 and key in instance_hash:
                return instance_hash[key]
            if key.vid != 0 and key in instance_hash_rewritten:
                return instance_hash_rewritten[key]
            raise(ConfigurationError(f"get_instance_by_key: {key} was not found."))
        except Exception as e:
            raise(e)
    
    @classmethod
    def exists(cls,
        key: InstanceKey, 
        instance_hash: Dict[InstanceKey, 'Instance']={},
        instance_hash_rewritten: Dict[InstanceKey, 'Instance']={}) -> bool:
        """Check whether an instance exists by querying its key.

        Parameters
        ----------
        key : InstanceKey
            The key of the intended instance.
        instance_hash : Dict[InstanceKey, Instance]
            A dict that saves all the *original* instances, by default None. 
            It denotes by the corresponding instance keys.
            If ``None``, resolve to ``Instance.instance_hash``.
        instance_hash_rewritten : Dict[InstanceKey, Instance]
            A dict that saves all the *rewritten* instances, by default None. 
            It denotes by the corresponding instance keys.
            If ``None``, resolve to ``Instance.instance_hash_rewritten``.

        Returns
        -------
        bool
            If the instance exists.
        """
        try:
            instance_hash = instance_hash or cls.instance_hash
            instance_hash_rewritten = instance_hash_rewritten or cls.instance_hash_rewritten
            if not key:
                return False
            if key.vid == 0 and key in instance_hash:
                return True
            if key.vid != 0 and key in instance_hash_rewritten:
                return True
            return False
        except Exception as e:
            return False

    @classmethod
    def create_instance_dict_given_qid(
        cls,
        qid: str, 
        qid_hash: Dict[str, InstanceKey]=None, 
        instance_hash: Dict[InstanceKey, 'Instance']=None,
        instance_hash_rewritten: Dict[InstanceKey, 'Instance']=None
        ) -> Dict[str, 'Instance']:
        # this function tries to create instance dict with a given qid
        output_dict = defaultdict(None)
        try:
            qid_hash = qid_hash or cls.qid_hash
            instance_hash = instance_hash or cls.instance_hash
            instance_hash_rewritten = instance_hash_rewritten or cls.instance_hash_rewritten
            if not qid:
                raise(ConfigurationError(f"create_instance_dict_given_qid: qid cannot be {qid} ({type(qid)})"))
            if qid not in qid_hash:
                raise(ConfigurationError(f"create_instance_dict_given_qid: {qid} was not found."))
            for key in qid_hash[qid]:
                try:
                    instance = cls.get(key, instance_hash, instance_hash_rewritten)
                    output_dict[instance.rid] = instance
                except Exception as e:
                    raise(e)
            return output_dict
        except Exception as e:
            raise(e)
    
    @classmethod
    def create_instance_dicts(
        cls,
        qid_hash: Dict[str, InstanceKey]=None, 
        instance_hash: Dict[InstanceKey, 'Instance']=None,
        instance_hash_rewritten: Dict[InstanceKey, 'Instance']=None
        ) -> Dict[str, 'Instance']:
        try:
            return [ Instance.create_instance_dict_given_qid(qid) for qid in Instance.qid_hash ]
        except Exception as e:
            raise(e)
    
    @classmethod
    def build_instance_hashes(cls, instances: List['Instance']) -> \
        Tuple[Dict[InstanceKey, 'Instance'], Dict[InstanceKey, 'Instance'], Dict[str, List[InstanceKey]]]:
        """
        Build the hases
        
        Parameters
        ----------
        instances : List[Instance]
            [description]
        
        Returns
        -------
        Tuple[Dict[InstanceKey, Instance], Dict[InstanceKey, Instance], Dict[str, List[InstanceKey]]]
            [description]
        """
        cls.instance_hash = {i.key(): i for i in instances if i.vid == 0 }
        cls.instance_hash_rewritten = {i.key(): i for i in instances if i.vid != 0 }
        cls.qid_hash = defaultdict(list)
        groups = groupby(sorted([ i.key() for i in instances ], 
                                key=lambda x: (x.qid, x.vid)), 
                        key=lambda x: x.qid)
        groups = [(key, list(val)) for key, val in groups]
        for qid, keys in groups:
            cls.qid_hash[qid] = keys
        return cls.instance_hash, cls.instance_hash_rewritten, cls.qid_hash

    @classmethod
    def save(cls, instance: 'Instance') -> bool:
        """
        Save an instance into the hash:  
        (``Instance.instance_hash``, ``Instance.instance_hash_rewritten``, 
        and ``Instance.qid_hash``)
        
        Parameters
        ----------
        instance : Instance
            The instance to be saved.
        
        Returns
        -------
        bool
            If the instance is correctly saved.
        """
        if not instance:
            raise(f"Instance not valid: {instance}")
        if instance.vid == 0:
            cls.instance_hash[instance.key()] = instance
        else:
            cls.instance_hash_rewritten[instance.key()] = instance
        if instance.key() not in cls.qid_hash[instance.qid]:
            cls.qid_hash[instance.qid].append(instance.key())
        return True
    
    @classmethod
    def remove_saved(cls, key: InstanceKey) -> bool:
        """Remove the saved instance from the hashes 
        (``Instance.instance_hash``, ``Instance.instance_hash_rewritten``, 
        and ``Instance.qid_hash``) by querying its key.
        
        Parameters
        ----------
        key : InstanceKey
            The key of the intended instance.
        
        Returns
        -------
        bool
            True if correctly removed (or not exist.)
        """
        try:
            if key in Instance.instance_hash:
                del Instance.instance_hash[key]
            if key in Instance.instance_hash_rewritten:
                del Instance.instance_hash_rewritten[key]
            if key.qid in Instance.qid_hash:
                Instance.qid_hash[key.qid] = [k for k in Instance.qid_hash[key.qid] if k != key]
            return True
        except Exception as e:
            raise(e)


    @classmethod
    def set_entry_keys(cls, entries: List[str]) -> None:
        """Save the target entry names used for a specific task to 
        ``Instance.instance_entries``.
        
        Parameters
        ----------
        entries : List[str]
            A list of entry names.
        """
        for key in entries:
            if key not in cls.instance_entries:
                cls.instance_entries.append(key)