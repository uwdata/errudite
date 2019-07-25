import math
import traceback
import numbers
from typing import Union, List
from spacy.tokens import Doc, Span, Token
from ...utils.helpers import convert_doc
from ...targets.target import Target
from ...utils.check import DSLValueError

from ..prim_func import PrimFunc


import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
from ..prim_func import PrimFunc

@PrimFunc.register()
def is_digit(target: Union[str, int, float]) -> bool:
    """
    Determines if an input is a number, or – in the case of a string
    input – if it can be parsed into a number.
    
    Parameters
    ----------
    target : Union[str, int, float]
        The input to check if is a digit.
        
    Returns
    -------
    bool
        Whether or not it's a digit.
    """
    output = False
    try:
        def is_digit_(doc):
            output_ = False
            if doc is None:
                raise DSLValueError("No input to [ is_digit ].")
            if isinstance(doc, numbers.Number):
                output_ = True
            elif isinstance(doc, str):
                try:
                    float(doc)
                    output_ = True
                except:
                    output_ = False
            elif isinstance(doc, Target):
                doc = convert_doc(doc, strict_format=True)
                output_ = len(doc) == 1 and doc[0].is_digit
            return output_
        if type(target) == list:
            output = any([ is_digit_(doc) for doc in target ]) # convert_token
        else:
            output = is_digit_(target) # convert_token
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ is_digit ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        #pass
        return output

@PrimFunc.register()
def digitize(target: Union[str, int, float]) -> Union[int, float]:
    """
    Parses an input into a number if ``is_digit(input) == True``;
    Otherwise returns ``None``.
    
    Parameters
    ----------
    target : Union[str, int, float]
        the input to be digitized.
    
    Returns
    -------
    Union[int, float]
        The digitized version of target. If not a number, return ``None``.
    """
    output = None
    try:
        def float_or_int(data):
            try:
                return int(data)
            except:
                return float(data)
        def digitize_(doc):
            output_ = None
            if (is_digit(doc)):
                if doc is None:
                    raise DSLValueError("No input to [ digitize ].")
                if isinstance(doc, numbers.Number):
                    output_ = doc
                elif isinstance(doc, str):
                    return float_or_int(doc)
                elif isinstance(doc, Target):
                    doc = convert_doc(doc, strict_format=True)
                    output_ = float_or_int(doc[0].text)
            return output_
        if type(target) == list:
            numbers_ = [ digitize_(doc) for doc in target ] # convert_token
            numbers_ = [ n for n in numbers_ if n is not None ]
            numbers_ = sorted(numbers_, key=lambda x: abs(x), reverse=True)
            if numbers_:
                output = numbers_[0]
        else:
            output = digitize_(target) # convert_token
        if output is None:
            raise DSLValueError(f"[ {target} ] cannot be digitized.")
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ digitize ]: {e}")
        #logger.error(ex)
        raise(ex)
    finally:
        return output

@PrimFunc.register()
def truncate(
    value: Union[int, float],
    min_value: Union[int, float]=-1, 
    max_value: Union[int, float]=50) -> int:
    """
    Clamps a given number to a given domain.
    
    Parameters
    ----------
    value : Union[int, float]
        The value to be clamped.
    min_value : Union[int, float], optional
        The minumum number allowed, by default -1
    max_value : Union[int, float], optional
        The maximum number allowed, by default 50
    
    Returns
    -------
    int
        The clamped value.
    """
    output = None
    try:
        if value is None:
            return None
        elif not is_digit(min_value):
            raise DSLValueError(f"Invalid value input to [ truncate ]: {value} ({type(value)}).")
        elif not is_digit(min_value) or not is_digit(max_value):
            raise DSLValueError(f"Invalid range input to [ truncate ]: {min_value} ({type(min_value)}), {max_value} ({type(max_value)}).")
        value, min_value, max_value = digitize(value), digitize(min_value), digitize(max_value)
        if value > max_value:
            output = max_value
        elif value < min_value:
            output = min_value
        else:
            output = value
    except DSLValueError as e:
        #logger.error(e)
        raise(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ digitize ]: {e}")
        #logger.error(ex)
        raise(ex)
    #finally:
    else:
        return output


@PrimFunc.register()
def abs_num(number: Union[int, float]) -> Union[int, float]:
    """ 
    Returns the absolute value.
    
    Parameters
    ----------
    number : Union[int, float]
        The input number.
    
    Returns
    -------
    Union[int, float]
        The output, absoluted number.
    """
    output = None
    try:
        if not is_digit(number):
            raise DSLValueError(f"Invalid value input to [ abs_num ]: {number} ({type(number)}).")
        number = digitize(number)
        output = abs(number)
    except DSLValueError as e:
        raise(e)
        #logger.error(e)
    except Exception as e:
        #print(f'[is_digit]')
        #traceback.print_exc()
        ex = Exception(f"Unknown exception from [ abs_num ]: {e}")
        logger.error(ex)
        raise(ex)
    #finally:
    else:
        return output