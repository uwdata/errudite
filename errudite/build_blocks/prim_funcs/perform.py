
import traceback
import functools
from typing import Union, List
from ...utils.helpers import convert_list
from ...targets.instance import Instance
from ...utils.check import DSLValueError
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

from ..prim_func import PrimFunc

@PrimFunc.register()
def perform(model: str, predictions: Union['Label', List['Label']], perform_name: str) -> float:
    """Get the specified performance metric for one instance, given the selected model.
    *When using the DSL parser*, this function can be called in alternative ways, 
    with ``perform_name`` being automatically filled in: 

    * ``[f1|exact match|precision|recall|accuracy|confidence]``, with get being the corresponding 
      metrics. Confidence is for usually the model prediction probability.
    * ``is_correct_sent``, with ``get=sent``.
    
    Parameters
    ----------
    model : str
        The model to query.
    predictions : Union[Label, List[Label]]
        All the predictions available.
        *Automatically filled in when using the DSL parser.*
    perform_name : str
        The selected metric name. It has to be a key that's in ``label.perform``.
    
    Returns
    -------
    float
        The queried metric.
    """
    output = 0
    try:
        model = Instance.resolve_default_model(model)
        if not model:
            raise DSLValueError(f"No valid model to [ perform ]. model: {model}")
        if not predictions:
            raise DSLValueError(f"No prediction input to [ perform ]. predictions: {predictions}")
        predictions = [ p for p in convert_list(predictions) if p.model == model ]
        if not predictions:
            raise DSLValueError(f"Cannot find [ model: {model} ]'s predictions for [ perform ].")
        output = predictions[0].get_perform(perform_name)
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ perform ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        #pass
        return output

for p in ["f1", "precision", "recall", "accuracy", "confidence", "exact_match"]:
    PrimFunc.register(p)(functools.partial(perform, perform_name=p))
PrimFunc.register("is_correct_sent")(functools.partial(perform, perform_name='sent'))