import traceback
import re
import numpy as np
import inspect
from typing import List, Dict, Callable
from collections import defaultdict
from .definitions import conditions as defConditions
from .operators import OpNode, OpNodeReturn

from ..targets.instance import Instance
from ..targets.interfaces import InstanceKey, UNREWRITTEN_RID

from ..utils.check import DSLValueError
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

class BuildBlockWrapper(object):
    def __init__(self):
        self.operator: OpNode = None
        self.cmd_type: str = ''
    
    def normalize_cmd(self, cmd):
        cmd = re.sub(r'[\n\t]+', ' ', cmd)
        cmd = re.sub(r'[\'|\“|\”]', '"', cmd)
        cmd = re.sub(r'[\']', '"', cmd)
        return cmd
    
    def _parse_cmd_func(self, cmd: Callable):
        if "rewrite_type" in inspect.signature(cmd).parameters:
            rewrite_type = inspect.signature(cmd).parameters["rewrite_type"].default
        else:
            rewrite_type = UNREWRITTEN_RID
        rewrite_type = Instance.resolve_default_rewrite(rewrite_type)
        def test_func(instance_group, **kwargs):
            try:
                instance = instance_group[rewrite_type]
                return OpNodeReturn(
                    key=[ instance.key() ],
                    value=cmd(instance, **kwargs))
            except Exception as e:
                ex = DSLValueError(f"Unknown exception caught in [ {cmd.__name__} ]: {e}")
                raise(ex)
        return test_func


    def parse_cmd_to_operator(self, cmd: str, cmd_type: str) -> None:
        """Parse the str cmd into an operator
        
        Arguments:
            cmd {str} -- the input string
            type {str} -- attr or filter
        
        Returns:
            None -- [description]
        """
        def parse_cmd(cmd: str) -> OpNode:
            try:
                cmd = self.normalize_cmd(cmd)
                parsed = defConditions.parseString(cmd)["conditions"]
                if isinstance(parsed, OpNode): 
                    return parsed
                elif parsed in Instance.instance_entries + ['groundtruth', 'prediction']:
                    return parsed
                else:
                    raise DSLValueError(f"Invalid parsing: [ {cmd} ]. {cmd_type} not correctly created!")
            except:
                #traceback.print_exc()
                raise DSLValueError(f"Invalid parsing: [ {cmd} ]. {cmd_type} not correctly created!")
        try:
            if not cmd:
                self.operator = True
            elif callable(cmd):
                self.operator = self._parse_cmd_func(cmd)
            elif type(cmd) == bool: # only save the bool
                self.operator = cmd
            else:
                self.operator = parse_cmd(cmd)
            logger.info(f"Parsed: {self.operator}")
        except DSLValueError as e:
            #logger.error(e)
            #self.operator = OpNode()
            raise(e)
        except Exception as e:
            #print(f'[is_digit]')
            #traceback.print_exc()
            self.operator = OpNode()
            ex = Exception(f"Unknown exception from [ parse_cmd ]: {e}")
            #logger.error(ex)
            raise(ex)
        else:
            self.cmd_type = cmd_type
    
    def test_instances(self, 
        instance_groups: List[Dict[str, Instance]], 
        attr_hash: Dict[str, 'Attribute']=None, 
        group_hash: Dict[str, 'Group']=None) -> list:
        """run the operation on a list of instances
        
        Arguments:
            func_dict {dict} -- the dict of the primitive function
            instance_dict_list {list} -- a list of instances
        
        Key Arguments:
            instance_type {str} -- qa or vqa {default: 'qa'}

        Returns:
            list -- [description]
        """
        output_ = {}
        try:
            id_list = defaultdict(None)
            for instance_group in instance_groups:
                instances = list(instance_group.values())
                if not instances:
                    continue
                default_key, keys = InstanceKey(qid=instances[0].qid, vid=0), None
                if isinstance(self.operator, OpNode):
                    output = self.operator.get_value(
                        attr_hash=attr_hash,
                        group_hash=group_hash,
                        instance_group=instance_group)
                    value = output.value
                    keys = list(set(output.key))
                elif callable(self.operator):
                    output = self.operator(
                        attr_hash=attr_hash,
                        group_hash=group_hash,
                        instance_group=instance_group)
                    value = output.value
                    keys = list(set(output.key))
                elif type(self.operator) == bool:
                    if self.operator:
                        keys = [ default_key ]
                    value = self.operator
                else:
                    value = self.operator
                
                if (self.cmd_type == 'attr' and value is not None) or value == True:
                    if keys and len(keys) == 1:
                        id_list[keys[0]] = value
                    else:
                        id_list[default_key] = value
            output_ = id_list
            return output_
        except DSLValueError as e:
            logger.error(e)
            # raise e
        except Exception as e:
            #print(f'[is_digit]')
            #traceback.print_exc()
            ex = Exception(f"Unknown exception from [ test_instances ]: {e}")
            logger.error(ex)
            raise(e)
        #finally:
            #pass
        #    return output_