from ..prim_func import PrimFunc
from typing import Callable, Any
@PrimFunc.register()
def apply(func: Callable, rewrite: str="SELECTED") -> Any:
    """
    Applies query functions to instances rewritten by the named rule rewrite.
    
    Parameters
    ----------
    func : Callable
        A query function.
    rewrite : str, optional
        Use a named rule rewrite to get instances rewritten by the rule.
        If using "SELECTED", it will be automatically resolved to 
        ``Instance.model`` , by default "SELECTED"
    
    Returns
    -------
    Any
        return the corresponding output format as the ``func``.
    """
    return func