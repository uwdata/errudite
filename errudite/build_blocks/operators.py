import traceback
import functools
from typing import Dict, NamedTuple, List
from collections import defaultdict

from .prim_func import PrimFunc
from ..targets.instance import Instance
from ..targets.interfaces import InstanceKey, UNREWRITTEN_RID

from ..utils.check import DSLValueError

class OpNodeReturn(NamedTuple):
    key: List[InstanceKey]
    value: any
DEFAULT_RETURN = OpNodeReturn([], None)


class OpNode(object):
    """The highest level class for the operators. Defines the get_value func.
    """
    def __eq__(self, other):
        if isinstance(other, OpNode):
            return self.__repr__() == other.__repr__()
        else:
            return False

    def rectify_value(self, value):
        if type(value) == str:
            value = f'"{value}"'
        return value
        #elif type(output) == list:
        #    output = [f'"{o}"' if type(o) == str else o for o in output]

    def get_value(self, **kwargs) -> OpNodeReturn:
        """get value function.
        
        Returns:
            {any} -- any kind
        """
        #print(Warning(f"[{self.__class__.__name__}]" + 
        #    " : This is a undefined class!"))
        return DEFAULT_RETURN

class NoneNode(OpNode):
    """The None value
    """
    def get_value(self, **kwargs) -> any:
        return DEFAULT_RETURN

class BuildBlockOp(OpNode):
    def __init__(self, tokens):
        while tokens[0].__class__.__name__ == 'ParseResults':
            tokens = tokens[0]
        self.type = tokens[0]
        self.name = tokens[1]
        self.built_block = None
    
    def get_value(self, 
        instance_group: Dict[str, Instance], 
        attr_hash: Dict[str, 'Attribute'], 
        group_hash: Dict[str, 'Group'], 
        rewrite_type: str=UNREWRITTEN_RID, **kwargs) -> OpNodeReturn:
        try:
            self.built_block = None
            if rewrite_type not in instance_group:
                return DEFAULT_RETURN
            instance = instance_group[rewrite_type]
            if self.type == 'attr' and attr_hash:
                if self.name in attr_hash:
                    self.built_block = attr_hash[self.name]
                    # get the value of this one instance
                    return OpNodeReturn (
                        key=[instance.key()], 
                        value=self.built_block.test_one_instance(
                            instance, attr_hash=attr_hash, group_hash=group_hash)
                    )
                return DEFAULT_RETURN
            elif self.type == 'group' and group_hash:
                if self.name in group_hash:
                    self.built_block = group_hash[self.name]
                    # get the key list for instances in the group
                    #print(self.built_block.get_instance_keys())
                    return OpNodeReturn (
                        key=[instance.key()], 
                        value=self.built_block.get_instances())
                return OpNodeReturn(key=[], value=[])
        except:
            raise

    def __repr__(self):
        return f"[{self.__class__.__name__}]({self.type}):{self.name}"

class LogicOp(OpNode):
    """The logic operators. Can be one or two operands.
    """

    def __init__(self, operator, operands):
        self.operator = operator
        self.operands = operands

    def __repr__(self) -> str:
        return f"[{self.__class__.__name__}]({self.operator}):{self.operands}"
    
    def _get_operand_value(self, 
        op, 
        instance_group: Dict[str, Instance],
        attr_hash: Dict[str, 'Attribute'], 
        group_hash: Dict[str, 'Group'], 
        rewrite_type: str=UNREWRITTEN_RID, **kwargs) -> list:
        """Convert the operand keys into values
        
        Returns:
            [list] -- A list of operand values
        """
        try:
            if isinstance(op, OpNode):
                return op.get_value(
                    instance_group=instance_group, 
                    attr_hash=attr_hash, 
                    group_hash=group_hash, 
                    rewrite_type=rewrite_type, **kwargs)
            elif type(op) == str:
                if rewrite_type not in instance_group:
                    return DEFAULT_RETURN
                instance = instance_group[rewrite_type]
                if op == 'instance':
                    return OpNodeReturn(
                        key=[instance.key()], 
                        value=instance.get_entry('instance'))
            return OpNodeReturn(key=[], value=op)
        except:
            raise
        
    def _get_operand_values(self, 
        instance_group: Dict[str, Instance],
        attr_hash: Dict[str, 'Attribute'], 
        group_hash: Dict[str, 'Group'], 
        rewrite_type: str=UNREWRITTEN_RID, **kwargs) -> List[OpNodeReturn]:
        """Convert the operand keys into values
        
        Returns:
            [list] -- A list of operand values
        """
        try:
            output = [self._get_operand_value(o, 
                instance_group=instance_group, 
                rewrite_type=rewrite_type,
                attr_hash=attr_hash, 
                group_hash=group_hash, **kwargs) for o in self.operands]
            return output
        except:
            raise
    
class UnOp(LogicOp):
    """The one operand operator: not|+|-
    """
    def __init__(self, tokens):
        LogicOp.__init__(self, tokens[0][0], [tokens[0][1]])
    
    def get_value(self, 
        instance_group: Dict[str, Instance],
        attr_hash: Dict[str, 'Attribute'], 
        group_hash: Dict[str, 'Group'], 
        rewrite_type: str=UNREWRITTEN_RID, **kwargs) -> OpNodeReturn:
        """Get the value of the operator
        
        Returns:
            {any} -- Any value needed to be returned.
        """
        try:
            operands = self._get_operand_values(
                instance_group=instance_group,
                rewrite_type=rewrite_type,
                attr_hash=attr_hash, group_hash=group_hash, **kwargs)
            if not operands or operands[0] == None or not isinstance(operands[0], OpNodeReturn):
                return OpNodeReturn([], False)
            elif operands[0].value == None and self.operator != 'not':
                return OpNodeReturn(operands[0].key, False)
            elif eval(f'{operands[0].value}') == None and self.operator != 'not':
                # print(f'{self.operands[0]} is None!!')
                return OpNodeReturn(operands[0].key, False)
            return OpNodeReturn(operands[0].key, eval(f"{self.operator}({operands[0].value})"))
        except:
            raise

class BinOp(LogicOp):
    """The one operand operator: in|+|-|>|<|>=|<=|and|or|==
    """
    def __init__(self, tokens):
        LogicOp.__init__(self, tokens[0][1], tokens[0][::2])
    
    def get_value(self, 
        instance_group: Dict[str, Instance],
        attr_hash: Dict[str, 'Attribute'], 
        group_hash: Dict[str, 'Group'], 
        rewrite_type: str=UNREWRITTEN_RID, **kwargs) -> OpNodeReturn:
        """Get the value of the operator
        
        Returns:
            {any} -- Any value needed to be returned.
        """
        try:
            #print(f'{operands[0]} {self.operator} {operands[1]}')
            output_keys = []
            if self.operator in ['and', 'or']:
                results = True if self.operator == 'and' else False
                for idx, op in enumerate(self.operands):
                    operand = self._get_operand_value(
                        op, 
                        instance_group=instance_group,
                        rewrite_type=rewrite_type,
                        attr_hash=attr_hash, group_hash=group_hash, **kwargs)
                    if operand == None or not isinstance(operand, OpNodeReturn):
                        return DEFAULT_RETURN
                    output_keys += operand.key
                    value = f'"{operand.value}"' if type(operand.value) == str else operand.value
                    if value == None:
                        return OpNodeReturn(output_keys, False)
                    cur_input = eval(f'{value}')
                    if cur_input == None:
                        #print(f'{self.operands[idx]} is None!!')
                        return OpNodeReturn(output_keys, False)
                    results = eval(f'{results} {self.operator} {cur_input}')
                    if results == True and self.operator == 'or':
                        return OpNodeReturn(output_keys, results)
                    if results == False and self.operator == 'and':
                        return OpNodeReturn(output_keys, results)
                return OpNodeReturn(output_keys, results)
            else:
                operands = self._get_operand_values(
                    instance_group=instance_group,
                    rewrite_type=rewrite_type,
                    attr_hash=attr_hash, group_hash=group_hash, **kwargs)
                if any([ o == None or not isinstance(o, OpNodeReturn) for o in operands ]) or \
                    len(self.operands) < 2:
                    return DEFAULT_RETURN
                key = operands[0].key + operands[1].key
                if self.operator == 'in':
                    return OpNodeReturn(key=key, 
                        value=operands[0].value in operands[1].value)
                elif self.operator == 'not in':
                    return OpNodeReturn(key=key, 
                        value=operands[0].value not in operands[1].value)
                operands = [OpNodeReturn(key=op.key, value=f'"{op.value}"') \
                    if type(op.value) == str else op for op in operands]
                #for idx, op in enumerate(operands):
                #    if op == None or not isinstance(op, OpNodeReturn) or eval(f'{op.value}') == None:
                #        # print(f'{self.operands[idx]} is None!!')
                #        return DEFAULT_RETURN
                try:
                    return OpNodeReturn(key=key,
                        value=eval(f'{operands[0].value} {self.operator} {operands[1].value}'))
                except:
                    return OpNodeReturn(key=key, value=False)
        except:
            raise

class KwargOp(OpNode):
    """operator used in a method. key=value
    """

    def __init__(self, tokens):
        self.key = tokens[0][0]
        self.value = tokens[0][1]
    def __repr__(self) -> str:
        return f"""{self.__class__.__name__}({self.key}):{self.value}"""

    def get_value(self, 
        instance_group: Dict[str, Instance],
        attr_hash: Dict[str, 'Attribute'], 
        group_hash: Dict[str, 'Group'], 
        rewrite_type: str=UNREWRITTEN_RID, **kwargs) -> OpNodeReturn:
        """Get the value of the operator
        
        Returns:
            dict -- (key, value) tuple
        """
        try:
            if isinstance(self.value, OpNode):
                output= self.value.get_value(
                    instance_group=instance_group, 
                    rewrite_type=rewrite_type,
                    attr_hash=attr_hash,
                    group_hash=group_hash, **kwargs)
                return OpNodeReturn(key=output.key, value=(self.key, output.value))
            else:
                if rewrite_type in instance_group:
                    instance = instance_group[rewrite_type]
                    if self.key != "target_type" and instance.get_entry(self.value) != None:
                        return OpNodeReturn(
                            key=[ instance.key() ],
                            value=(self.key, instance.get_entry(self.value)))
            return OpNodeReturn(key=[], value=(self.key, self.value))
        except:
            raise

class ArgOp(OpNode):
    """operator used in a method. value
    """

    def __init__(self, tokens):
        self.key = tokens[0][0]
    def __repr__(self) -> str:
        return "{}:{}".format(self.__class__.__name__, self.key)
    
    def get_value(self, 
        instance_group: Dict[str, Instance],
        attr_hash: Dict[str, 'Attribute'], 
        group_hash: Dict[str, 'Group'], 
        rewrite_type: str=UNREWRITTEN_RID, **kwargs) -> OpNodeReturn:
        """Get the value of the operator
        
        Arguments:
            function {str} -- the function name of the arg
            instance {Instance} -- the primitive targes
        
        Returns:
            any -- any data
        """
        try:
            if isinstance(self.key, OpNode):
                return self.key.get_value(
                    instance_group=instance_group, 
                    rewrite_type=rewrite_type,
                    attr_hash=attr_hash,
                    group_hash=group_hash, **kwargs)
            else:
                if rewrite_type in instance_group:
                    instance = instance_group[rewrite_type]
                    if instance.get_entry(self.key) != None:
                        return OpNodeReturn(
                            key=[ instance.key() ],
                            value=instance.get_entry(self.key))
            return OpNodeReturn(key=[], value=self.key)
        except:
            raise
    
class FuncOp(OpNode):
    def __init__(self, tokens):
        self.func_name = tokens[0][0]
        args = tokens[0][1]
        kwargs = [a for a in args if a.__class__.__name__ == 'KwargOp' ]
        self.kwargs = [ a for a in kwargs if a.key != 'rewrite' ]
        self.args = [a for a in args if a.__class__.__name__ != 'KwargOp' ]
        rewrite_kwargs = [ a for a in kwargs if a.key == 'rewrite' and type(a.value) == str ]
        if rewrite_kwargs:
            self.rewrite_type = rewrite_kwargs[0].value
        else:
            self.rewrite_type = UNREWRITTEN_RID

    def get_value(self, 
        instance_group: Dict[str, Instance],
        attr_hash: Dict[str, 'Attribute'], 
        group_hash: Dict[str, 'Group'],
        rewrite_type: str=UNREWRITTEN_RID, **kwargs):
        """Get the value of the operator
        
        Arguments:
            primitive_funcs {dict} -- {func_name: func}
        
        Returns:
            any -- any data
        """
        try:
            #print(self.args)
            #print([type(a) for a in self.args])
            # if the input type is the default, but we know it should not be default
            # overwrite
            if self.rewrite_type != UNREWRITTEN_RID and rewrite_type == UNREWRITTEN_RID:
                rewrite_type = self.rewrite_type
            # compute the instance in this case, in order to compute t
            rewrite_type = Instance.resolve_default_rewrite(rewrite_type)
            if rewrite_type not in instance_group:
                return DEFAULT_RETURN
            instance = instance_group[rewrite_type]
            instance_keys = []
            args_output = [a.get_value(
                    instance_group=instance_group,
                    rewrite_type=rewrite_type,
                    attr_hash=attr_hash,
                    group_hash=group_hash, **kwargs) if isinstance(a, OpNode) else a \
                for a in self.args]
            kwargs_arr_output = [
                a.get_value(
                    instance_group=instance_group,
                    rewrite_type=rewrite_type,
                    attr_hash=attr_hash,
                    group_hash=group_hash, **kwargs) for a in self.kwargs
            ]
            for a in args_output:
                instance_keys += a.key
            args = [ a.value for a in args_output ]
            kwargs = {}
            for a in kwargs_arr_output:
                instance_keys += a.key
                kwargs[a.value[0]] = a.value[1]
            func = PrimFunc.build_instance_func(self.func_name, instance)
            if not func:
                return DEFAULT_RETURN
            return OpNodeReturn(key=instance_keys, value=func(*args, **kwargs))
        except:
            raise
    
    def __repr__(self):
        return f"""{self.__class__.__name__}({self.func_name}):{self.args}+{self.kwargs}"""