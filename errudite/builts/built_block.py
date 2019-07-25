import os
from typing import Dict, List, Tuple, Callable, Union
from ..build_blocks.wrapper import BuildBlockWrapper
from ..targets.interfaces import InstanceKey
from ..targets.instance import Instance
from ..utils import DSLValueError, Store, CACHE_FOLDERS, dump_json
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
from ..utils import str_to_func, func_to_str


class BuiltBlock(Store):
    """
    A wrapping class for Groups and Attributes.
        
    Parameters
    ----------
    name : str
        The attribute/group name.
    description : str
        The description of the attribute/group.
    cmd : Union[str, Callable]
        The command that extracts attributes from instances / 
        filter instances to form groups.
        If it's a string, it's parsed by the DSL to actual functions.
        If the input is a function already, it's directly called 
        to get the attribute.
    
    Attributes
    ----------
    instance_dict : Dict[InstanceKey, Union[bool, float, str]]
        The instance dict that saves the attribute or whether or not
        an instance belongs to the group via their key.
    """
    def __init__(self, 
        name: str, # name the hypothesis
        description: str, # a brief description
        cmd: Union[str, Callable]):
        Store.__init__(self)
        self.cmd = ''
        self.name = name
        self.test_size = 0
        self.description = description
        self.instance_dict = {}
        self.bbw = BuildBlockWrapper()

    def size(self) -> int:
        """Return the size of the instances
        
        Returns
        -------
        int
            The instances saved.
        """
        return len(self.get_instances())

    def get_instances(self) -> Dict[InstanceKey, Union[bool, float, str]]:
        """
        Get the instance dict.
        
        Returns
        -------
        Dict[InstanceKey, Union[bool, float, str]]
            The instance dict.
        """
        return self.instance_dict
    
    def reset(self):
        """Reset the object, by setting the cmd and the instance_dict to be empty.
        """
        self.cmd = ''
        self.instance_dict = {}

    def should_recompute(self, switched: str) -> bool:
        """Whether or not a built block needs to be recomputed,
        based on whether or not the selected model or the rewrite rule
        is switched, and that whether or not the attribute/group depends
        on "ANCHOR" model or "SELECTED" rule.
        
        Parameters
        ----------
        switched : str
            ``model`` or ``rewrite``.
        
        Returns
        -------
        bool
            Should recompute or not.
        """
        if not switched:
            return False
        return type(self.cmd) == str and \
            ((switched == "model" and "ANCHOR" in self.cmd) or \
            (switched == "rewrite" and "SELECTED" in self.cmd))

    def set_cmd(self, cmd: Union[str, Callable], cmd_type: str) -> None:
        """
        Use the cmd to define the built block.
        
        Parameters
        ----------
        cmd : Union[str, Callable]
            The command that extracts attributes from instances / 
            filter instances to form groups.
            If it's a string, it's parsed by the DSL to actual functions.
            If the input is a function already, it's directly called 
            to get the attribute.
        cmd_type : str
            ``attr`` or ``group``.
        
        Returns
        -------
        None
        """
        try:
            cmd = str_to_func(cmd)
            self.bbw.parse_cmd_to_operator(cmd, cmd_type)
        except DSLValueError as e:
            #logger.error(e)
            raise(e)
        except Exception as e:
            #traceback.print_exc()
            ex = Exception(f"Unknown exception from [ set_cmd ]: {e}")
            #msg = ex.args
            #logger.error(ex)
            raise(ex)
        else:
            self.cmd = cmd

    def get_json(self) -> Dict[str, str]:
        """Get the json version definition of the built block.
        
        Returns
        -------
        Dict[str, str]
            The json version definition of the built block, with:
            name, cmd, and description in a dict.
        """
        return {
            'cmd': func_to_str(self.cmd),
            'name': self.name,
            'description': self.description
        }
    
    def get_existing_instance_key(self, 
        instance_group: Dict[str, Instance], 
        instance_hash: Dict[InstanceKey, Instance]) -> InstanceKey:
        """
        Check whether or not any version of an instance
        is saved in the ``instance_hash``.
        
        Parameters
        ----------
        instance_group : Dict[str, Instance]
            All the versions of one instance saved in one dict.
            Needs to be ``{ rid: InstanceKey }``
        instance_dict : Dict[InstanceKey, Instance]
            The instance hash that saves all the instances in a dict.
            Needs to be ``{ InstanceKey: Instance }``
         
        Returns
        -------
        InstanceKey
            If any version exists, return the key of that version.
            Otherwise, return ``None``.
        """
        if not instance_hash:
            return None
        for i in instance_group.values():
            if i.key() in instance_hash:
                return i.key()
        return None