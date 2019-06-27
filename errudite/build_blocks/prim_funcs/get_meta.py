import traceback
import functools
from typing import Any
from ...utils.helpers import convert_list
from ...targets.target import Target
from ...utils.check import DSLValueError
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
from ..prim_func import PrimFunc

@PrimFunc.register()
def get_meta(target: "Target", meta_name: str) -> Any:
    """
    Query the extra meta in a target.
    
    Parameters
    ----------
    target : Target
        A given target object.
    meta_name : str
        The name of the metadata. Has to be a key in ``target.metas``.
    
    Returns
    -------
    Any
        The queried meta.
    """
    output = None
    try:
        if not target or not isinstance(target, Target):
            raise DSLValueError(f"Invalid input to [ get_meta ]: {target} ({type(target)}) is not a Target object.")
        return target.get_meta(meta_name)
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        ex = Exception(f"Unknown exception from [ get_meta ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        return output