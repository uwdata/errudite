
import traceback
from typing import Union, List
from ...utils.helpers import convert_list
from ...targets.instance import Instance

from ...utils.check import DSLValueError
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
from ..prim_func import PrimFunc

@PrimFunc.register()
def prediction(model: str, predictions: Union['Label', List['Label']]) -> 'Label':
    """
    Get the prediction object of a given model.
    
    Parameters
    ----------
    model : str
        The model to query.
    predictions : Union[Label, List[Label]]
        All the predictions available.
        *Automatically filled in when using the DSL parser.*
        
    Returns
    -------
    Label
        The selected prediction.
    """

    output = None
    try:
        model = Instance.resolve_default_model(model)
        if not model:
            raise DSLValueError(f"No valid model to [ prediction ]. model: {model}")
        if not predictions:
            raise DSLValueError(f"No prediction input to [ prediction ]. predictions: {predictions}")
        predictions = [ p for p in convert_list(predictions) if p.model == model ]
        if not predictions:
            raise DSLValueError(f"Cannot find [ model: {model} ]'s predictions for [ prediction ].")
        output = predictions[0]
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ prediction ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        #pass
        return output