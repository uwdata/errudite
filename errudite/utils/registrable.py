from collections import defaultdict
from typing import TypeVar, Type, Dict, List, Callable
import logging
from .from_params import FromParams
from .check import ConfigurationError
from functools import partial

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

T = TypeVar('T')

class Registrable(FromParams):
    """
    Adjusted from https://allenai.github.io/allennlp-docs/api/allennlp.common.registrable.html.
    Any class that inherits from ``Registrable`` gains access to a named registry for its
    subclasses. To register them, just decorate them with the classmethod
    ``@BaseClass.register(name)``.
    After which you can call ``BaseClass.list_available()`` to get the keys for the
    registered subclasses, and ``BaseClass.by_name(name)`` to get the corresponding subclass.
    Note that the registry stores the subclasses themselves; not class instances.

    Note that if you use this class to implement a new ``Registrable`` abstract class,
    you must ensure that all subclasses of the abstract class are loaded when the module is
    loaded, because the subclasses register themselves in their respective files. You can
    achieve this by having the abstract class and all subclasses in the ``__init__.py`` of the
    module in which they reside (as this causes any import of either the abstract class or
    a subclass to load all other subclasses and the abstract class).
    """
    _registry: Dict[Type, Dict[str, Type]] = defaultdict(dict)
    default_implementation: str = None

    @classmethod
    def register(cls: Type[T], name: str=None) -> Callable:
        """
        A decorator function that helps register sub-classes/sub-functions:
        ``@BaseClass.register(name)``
        
        Parameters
        ----------
        cls : Type[T]
            The base class
        name : str, optional
            The name of the subclass. If not given retrive the name of the subclasses/functions. 
            By default None
        
        Returns
        -------
        Callable 
            The registering function
        """
        registry = Registrable._registry[cls]
        def add_subclass_to_registry(subclass: Type[T], name):
            # Add to registry, raise an error if key has already been used.
            if not name:
                name = subclass.__name__
            if name in registry:
                message = "Register %s as %s: Overwritting name already in use for %s." % (
                        name, cls.__name__, registry[name].__name__)
                #raise ConfigurationError(message)
                logger.warning(message)
            registry[name] = subclass
            return subclass
        return partial(add_subclass_to_registry, name=name)

    @classmethod
    def by_name(cls: Type[T], name: str) -> Type[T]:
        """
        Get the sub-class/sub-function by their registered name.
        
        Parameters
        ----------
        cls : Type[T]
            The base class.
        name : str
            The name of the subclass/sub-function.
        
        Returns
        -------
        Type[T]
            sub-class/sub-function 
        """
        logger.debug(f"instantiating registered subclass {name} of {cls}")
        if name not in Registrable._registry[cls]:
            raise ConfigurationError("%s is not a registered name for %s" % (name, cls.__name__))
        return Registrable._registry[cls].get(name)

    @classmethod
    def list_available(cls) -> List[str]:
        """
        List all the available sub-class/functions available in an abstracted class.
        
        Returns
        -------
        List[str]
            The string list of all the sub-class/and sub-functions.
        """
        keys = list(Registrable._registry[cls].keys())
        default = cls.default_implementation

        if default is None:
            return keys
        elif default not in keys:
            message = "Default implementation %s is not registered" % default
            raise ConfigurationError(message)
        else:
            return [default] + [k for k in keys if k != default]