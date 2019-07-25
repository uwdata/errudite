import traceback
from typing import List, Any
from ...utils.helpers import convert_list
from ...utils.check import DSLValueError
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
from ..prim_func import PrimFunc



@PrimFunc.register()
def has_any(container: List[Any], contained: List[Any]) -> bool:
    """
    Determines whether one list container contains any
    of the members present in another lists.

    Parameters
    ----------
    container : List[Any]
        The container list, or the super set.
    contained : List[Any]
        The contained list, or the subset.
    
    Returns
    -------
    bool
        If the 'any' condition holds.
    """
    output = False
    try:
        if not container or not contained:
            pass
        output = any([ c in convert_list(container) for c in convert_list(contained) ])
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ has_any ]: {e}")
        #logger.error(ex)
        raise(ex)
    else:
        return output

@PrimFunc.register()
def has_all(container: List[Any], contained: List[Any]) -> bool:
    """
    Determines whether one list container contains all
    of the members present in another lists.

    Parameters
    ----------
    container : List[Any]
        The container list, or the super set.
    contained : List[Any]
        The contained list, or the subset.
    
    Returns
    -------
    bool
        If the 'all' condition holds.
    """
    output = False
    try:
        if not container:
            container = []
        if not contained:
            contained = []
        output = all([ c in convert_list(container) for c in convert_list(contained) ])
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ has_all ]: {e}")
        #logger.error(ex)
        raise(ex)
    else:
        return output

@PrimFunc.register()
def count(vars: List[Any]) -> int:
    """Count the number of members in the input list.
    
    Parameters
    ----------
    vars : List[Any]
        The vars to be counted.
    
    Returns
    -------
    int
        The counted number.
    """
    output = 0
    try:
        if not vars:
            output = 0
        else:
            output = len(convert_list(vars))
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ count ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        return output