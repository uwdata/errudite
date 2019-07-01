from inspect import signature
from functools import partial
from typing import Callable, Dict, List
from ..utils import Registrable
from ..targets.instance import Instance
from ..utils.check import DSLValueError

class PrimFunc(Registrable):
    """
    A wrapper function primitive functions used in the domain specific language.
    It inherits ``errudite.utils.registrable``, so all the functions can be 
    registered to this class with their function names.
    """
    def __init__(self):
        pass
    
    @classmethod
    def build_instance_func(cls, func_name: str, instance: 'Instance') -> Callable:
        """
        Given an instance, adjust the one function to fit specifically for that instance.
        It does it by automatically filling in the inputs that have the same variable 
        name as a target entry in the instance, so users could write the DSL function 
        more easily.
        
        Parameters
        ----------
        func_name : str
            The name of the function.
        instance : Instance
            The instance that all the function should be adjusted to.
        
        Returns
        -------
        Callable
            The functions with entries filled in.
        """
        try:
            params = {}
            func = PrimFunc.by_name(func_name)
            sig = signature(func)
            for param_name, param in sig.parameters.items():
                instance_data = instance.get_entry(param_name)
                if instance_data is not None:
                    params[param_name] = instance_data
                # TODO: check if this is useful. 
                #elif param.default is not param.empty:
                #    params[param_name] = param.default
            return partial(func, **params)
        except:
            raise

    @classmethod
    def build_instance_func_list(cls, instance: 'Instance') -> Dict[str, Callable]:
        """
        Given an instance, adjust the all the functions to fit specifically for that instance.
        It does it by automatically filling in the inputs that have the same variable 
        name as a target entry in the instance, so users could write the DSL function 
        more easily.
        
        Parameters
        ----------
      instance : Instance
            The instance that all the function should be adjusted to.
        
        Returns
        -------
        Dict[str, Callable]
            A dict of functions, with each function being partially filled in (i.e. users
            only need to fill in variables whose name do not occur in the entries of instances.)
        """
        instance_funcs = {}
        for func_name in PrimFunc.list_available():
            instance_funcs[func_name] = PrimFunc.build_instance_func(func_name, instance)
        return instance_funcs
    
    @classmethod
    def get_funcs_hash(cls) -> Dict[str, List[str]]:
        """
        This is an inspection function. By calling this, we construct a dict 
        that presents ``{ func_name : [ args ] }``, to show what functions are
        available, and what arguments and keyword arguments needed.
        
        Returns
        -------
        Dict[str, List[str]]
            The inspection dict hash.
        """
        entries = Instance.instance_entries + [ "prediction", "groundtruth" ]
        instance_params = {}
        for func_name in PrimFunc.list_available():
            func = PrimFunc.by_name(func_name)
            sig = signature(func)
            instance_params[func_name] = [  ]
            for param in sig.parameters.values():
                if param.name in entries:
                    continue
                if param.default is param.empty:
                    instance_params[func_name].append(param.name)
                elif isinstance(func, partial) and param.name in func.keywords:
                    continue
                else:
                    value = f'"{param.default}"' if type(param.default)==str \
                        else param.default
                    instance_params[func_name].append(f'{param.name}={value}')
        return instance_params