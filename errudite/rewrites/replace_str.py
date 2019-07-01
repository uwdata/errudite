from typing import List, Dict
from spacy.tokens import Token


from .rewrite import Rewrite
from ..targets.instance import Instance

#from backend.utils.helpers import convert_list
#from backend.build_block.prim_funcs.overlap import overlap
from ..build_blocks.wrapper import BuildBlockWrapper

@Rewrite.register("ReplaceStr")
class ReplaceStr (Rewrite):
    """
    A rule that rewrites the target_cmd part of an instance 
    by replacing from_cmd with to_cmd. The rid is: ``{from_cmd} -> {to_cmd}``.
    
    The from_cmd and to_cmd can both ONLY BE EXACT STRINGS that you want to replace from/to.
    If you want to use linguistic patterns (e.g., ``from_cmd="what NOUN"``), use
    ``errudite.rewrites.replace_pattern.ReplacePattern``.

    An easier way might be to stick to ``ReplaceStr`` -- It detects whether the linguistic 
    patterns are used automatically. If not, it will automatically switch to  ``ReplaceStr``.

    .. code-block:: python

        from errudite.rewrites import Rewrite
        Rewrite.by_name("ReplaceStr")
    
    Parameters
    ----------
    from_cmd : str, optional
        The pattern that can be replaced. By default ''
    to_cmd : str, optional
        The pattern to replace to, by default ''
    description : str, optional
        The description, by default 'Change one pattern to another.'
    target_cmd : str, optional
        The target to be rewritten. It has to be a member of ``Instance.instance_entries``, 
        by default 'context'
    """
    def __init__(self,
        from_cmd: str='',
        to_cmd: str='',
        rid: str='', # name the hypothesis
        description: str='Replace one string with another.', # a brief description
        target_cmd: str='context', **kwargs):
        rid = f'{from_cmd} -> {to_cmd}'
        Rewrite.__init__(self, rid, 'auto', description, target_cmd)
        self.from_cmd = from_cmd
        self.to_cmd = to_cmd
        self.bbw_from = BuildBlockWrapper()
        try:
            self.bbw_from.parse_cmd_to_operator(from_cmd, 'attr')
        except:
            pass
        self.bbw_to = BuildBlockWrapper()
        try:
            self.bbw_to.parse_cmd_to_operator(to_cmd, 'attr')
        except:
            pass
    
    def is_pure_str_replace(self):
        return True

    def _rewrite_target(self, instance: Instance) -> str: 
        # if the editing happened.
        ori_str = self._get_target(instance)
        if ori_str:
            ori_str = ori_str.text
        else:
            return None
        try:
            from_data = self.bbw_from.test_instances([{ instance.rid: instance }])
            from_str = from_data[instance.key()] if instance.key()  in from_data and from_data[instance.key()] != None else self.from_cmd
        except:
            from_str = self.from_cmd
        try:
            to_data = self.bbw_to.test_instances([{ instance.rid: instance }])
            to_str = to_data[instance.key()] if instance.key()  in to_data and to_data[instance.key()] != None else self.to_cmd
        except:
            to_str = self.to_cmd
        if from_str != None and to_str != None:
            return ori_str.replace(from_str, to_str)
        return None
    
    def get_json(self):
        return {
            'rid': self.rid,
            'category': self.category,
            'from_cmd': self.from_cmd,
            'to_cmd': self.to_cmd,             
            'description': self.description,
            'target_cmd': self.target_cmd,
            'class': self.__class__.__name__
        }