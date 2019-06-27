
import os
import logging
import shutil
import tempfile
import json
from urllib.parse import urlparse
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

from typing import List
import json
import dill as pickle

DEFAULT_CACHE_FOLDER = './caches/'
CACHE_FOLDERS = {
    "cache": DEFAULT_CACHE_FOLDER,
    "analysis": os.path.join(DEFAULT_CACHE_FOLDER, 'analysis/'),
    "evaluation": os.path.join(DEFAULT_CACHE_FOLDER, 'evaluations/')
}

def set_cache_folder(cache_path):
    global CACHE_FOLDERS
    CACHE_FOLDERS["cache"] = os.path.expanduser(cache_path)
    CACHE_FOLDERS["analysis"] = os.path.join(CACHE_FOLDERS["cache"], 'analysis/')
    CACHE_FOLDERS["evaluations"] = os.path.join(CACHE_FOLDERS["cache"], 'evaluations/')
    if not os.path.exists(CACHE_FOLDERS["cache"]):
        os.makedirs(CACHE_FOLDERS["cache"])
    # create the evaluation file
    if not os.path.exists(CACHE_FOLDERS["evaluations"]):
        os.makedirs(CACHE_FOLDERS["evaluations"])
    # create the analysis file
    if not os.path.exists(CACHE_FOLDERS["analysis"]):
        os.makedirs(CACHE_FOLDERS["analysis"])
    logger.info(f'Errudite cache folder selected: {CACHE_FOLDERS["cache"]}')

def load_json(filepath: str) -> any:
    """Load a json file
    
    Arguments:
        filepath {str} -- file path string
    
    Returns:
        [type] -- whatever type the file has
    """
    try:
        with open(filepath) as cur_file:
            data = json.load(cur_file)
        return data
    except Exception as e:
        raise(e)

def dump_json(data: any, filepath: str, is_compact: bool=False) -> None:
    """Save data into a json file.
    
    Arguments:
        filepath {str} -- file path string
        data {Any} -- any data
    
    Keyword Arguments:
        is_compact {bool} -- if we use indents in the json file (default: {False})
    
    Returns:
        None -- Nothing returned
    """
    try:
        indent = None if is_compact else 4
        with open(filepath, 'w') as cur_file:
            cur_file.write(json.dumps(data, indent=indent))
    except Exception as e:
        raise(e)

def dump_caches(obj: any, cache_filepath: str) -> None:
    """[summary]
    
    Arguments:
        obj {Any} -- any data
        cache_filepath {str} -- file path string
    
    Returns:
        None -- Nothing returned
    """
    try:
        pickle.dump(obj, open(cache_filepath, 'wb'))
    except Exception as e:
        raise(e)

def load_caches(cache_filepath: str) -> any:
    """Load caches
    
    Arguments:
        cache_filepath {str} -- file path
    
    Returns:
        Any -- any data type
    """
    try:
        with open(cache_filepath, "rb") as f:
            return pickle.load(f)
    except Exception as e: 
        raise(e)

def normalize_file_path(data_path: str) -> str:
    return os.path.abspath(os.path.expanduser(data_path))

def build_cached_path(url_or_filename: str, cache_dir: str = None) -> str:
    """
    Given something that might be a URL (or might be a local path),
    determine which. If it's a URL, download the file and cache it, and
    return the path to the cached file. If it's already a local path,
    make sure the file exists and then return the path.
    """
    if cache_dir is None:
        cache_dir = CACHE_FOLDERS["cache"]
    url_or_filename = str(url_or_filename)
    # get cache path to put the file
    cache_path = normalize_file_path(os.path.join(cache_dir, url_or_filename))
    if os.path.exists(cache_path):
        # File, and it exists.
        return cache_path
    else:
        # Something unknown
        logger.warning("Local path not yet exist, but still parsed: {}".format(cache_path))
        return cache_path
#set_cache_folder(CACHE_FOLDERS["cache"])