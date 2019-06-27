import os
from collections import defaultdict
from typing import Any, TypeVar, Tuple, Type, Dict, List, Iterable
import logging
from .from_params import FromParams
from .check import ConfigurationError
from functools import partial

from ..utils.file_utils import CACHE_FOLDERS, dump_json, load_json, normalize_file_path

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

T = TypeVar('T')

class Store(object):
    """A store wrapper class. Children of this class 
    allow actual objects to be saved in 
    ``Store._store_hash[cls] = { object_key: object }``.
    We provide functions that helpes the Store class to be
    used mostly like a normal ``dict`` object.
    """
    
    #: ``Dict[Type, Dict[str, T]]`` The store hash.
    _store_hash: Dict[Type, Dict[str, T]] = defaultdict(dict)

    @classmethod
    def store_hash(cls) -> Dict[str, T]:
        """
        Return the store hash as a dict.
        
        Returns
        -------
        Dict[str, T]
        """
        return Store._store_hash[cls._reset_name()]
    

    @classmethod
    def _reset_name(cls):
        if "Rewrite" in cls.__name__ or cls.__name__ in ["ReplacePattern", "ReplaceStr", "SemanticRule", ]:
            return "Rewrite"
        return cls.__name__

    @classmethod
    def keys(cls) -> Iterable[str]:
        """
        Return the keys of the store hash as a generator.
        
        Returns
        -------
        Iterable[str]
            The generator of the keys
        """
        return Store._store_hash[cls._reset_name()].keys()
    @classmethod
    def values(cls) -> Iterable[T]:
        """
        Return the values of the store hash as a generator.
        
        Returns
        -------
        Iterable[T]
            The generator of the values
        """
        return Store._store_hash[cls._reset_name()].values()
    @classmethod
    def items(cls) -> Iterable[Tuple[str, T]]:
        """
        Return the items of store hash as a generator of
        tuples of ``(key, val)``.
        
        Returns
        -------
        Iterable[Tuple[str, T]]
            The generator of the tuples of keys and values.
        """
        return Store._store_hash[cls._reset_name()].items()
    @classmethod
    def get(cls, name: str) -> T:
        """Get the stored object by querying its name.

        Parameters
        ----------
        name : str
            The name of the intended stored object.

        Returns
        -------
        T
            The queried object.
        """
        if name not in Store._store_hash[cls._reset_name()]:
            raise ConfigurationError("%s is not in the store of %s" % (name, cls._reset_name()))
        return Store._store_hash[cls._reset_name()].get(name)
    @classmethod
    def exists(cls, name: str) -> bool:
        """
        Check with the stored object exist, by querying its name.

        Parameters
        ----------
        name : str
            The name of the intended stored object.

        Returns
        -------
        bool
            If the instance exists.
        """
        return name is not None and name in Store._store_hash[cls._reset_name()]

    @classmethod
    def create_from_json(cls, raw: Dict[str, Any]) -> T:
        """Recreate the object from its seralized raw json file.
        
        Parameters
        ----------
        raw : Dict[str, Any]
            The raw version of the object.

        Returns
        -------
        T
            The re-created object.
        
        Raises
        ------
        NotImplementedError
            This function is supposed to be implemented 
        """
        raise NotImplementedError

    @classmethod
    def import_from_file(cls, file_name: str) -> Dict[str, T]:
        """
        Import the saved store frome a file. It recovers all the saved,
        json version of objects, and save them to the store_hash. 
        
        Parameters
        ----------
        file_name : str
            The name of the json file. It should be a file in 
            ``CACHE_FOLDERS["analysis"]``.
        
        Returns
        -------
        Dict[str, T]
            The restored hash, or ``Store._store_hash[cls]``.
        """
        try:
            if not file_name:
                raise(ConfigurationError(f"import_from_file [ {cls._reset_name()} ]: No file given."))
            if not file_name.endswith('.json'):
                file_name += '.json'
            raws = load_json(os.path.join(CACHE_FOLDERS["analysis"], file_name))
            if raws:
                for raw in raws:
                    built = cls.create_from_json(raw)
                    cls.save(built)
            return cls.store_hash()
        except Exception as e:
            raise(e)
    
    @classmethod
    def export_to_file(cls, file_name: str) -> bool:
        """Export the store hash ``Store._store_hash[cls]`` to
        json file.
        
        Parameters
        ----------
        file_name : str
            The name of the json file. It will save to a file:
            ``{CACHE_FOLDERS["analysis"]}/{file_name}.json``.
        
        Returns
        -------
        bool
            Whether or not the export is successful.
        """
        try:
            if not file_name.endswith('.json'):
                file_name += '.json'
            dump_json( 
                [b.get_json() for b in cls.values()],
                os.path.join(CACHE_FOLDERS["analysis"], file_name))
            logger.info("Done saving to " + os.path.join(CACHE_FOLDERS["analysis"], file_name))
            return True
        except:
            raise
    
    @classmethod
    def save(cls, obj: T) -> bool:
        """Save the object to the store hash.
        
        Parameters
        ----------
        obj : T
            The object to be saved.
        
        Returns
        -------
        bool
            Whether or not the export is successful.
        """
        name = getattr(obj, "name", None) or getattr(obj, "rid", None)
        if name in Store._store_hash[cls._reset_name()]:
            message = "Storing %s in %s: Overwritting name already in use." % (
                name, cls._reset_name())
                #raise ConfigurationError(message)
            logger.warning(message)
        Store._store_hash[cls._reset_name()][name] = obj
        return True

    @classmethod
    def _remove_by_name(cls, name: str) -> bool:
        """Remove the object from the store hash by querying its name.
        
        Parameters
        ----------
        name : str
            The name of the intended stored object.

        Returns
        -------
        bool
            If the removal is successful.
        """
        try:
            if cls.exists(name):
                del Store._store_hash[cls._reset_name()][name]
                logger.info(f'Removed {cls._reset_name()}: {name}.')
                return True
            else:
                raise(ConfigurationError(f'Not existing {cls._reset_name()}: {name}.'))
            return False
        except:
            raise
    @classmethod
    def remove_saved(cls, name: str) -> bool:
        """Remove the object from the store hash by querying its name.
        
        Parameters
        ----------
        name : str
            The name of the intended stored object.

        Returns
        -------
        bool
            If the removal is successful.
        """
        return cls._remove_by_name(name)