import os
import sys
import yaml
import requests

sys.path.append("..")
sys.path.append("../..")
import base64
import traceback
import argparse
from typing import List
from zipfile import ZipFile
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

def get_args():
    """Get the user arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache_folder_name', 
        required=True, 
        help='The cache folder name that you would like to download.')
    parser.add_argument('--cache_path', 
        required=True, 
        help='Save the folder to a given place.')
    args = parser.parse_args()
    return args

args = get_args()
try:
    cache_folder_name = args.cache_folder_name if args.cache_folder_name.endswith(".zip") else f'{args.cache_folder_name}.zip'
    file_url = "https://errudite.s3.us-east-2.amazonaws.com/" + cache_folder_name
    file = requests.get(file_url)
    cache_path = args.cache_path
    total_cache_path = os.path.join(cache_path, cache_folder_name)
    with open(total_cache_path, 'wb') as f: 
        f.write(file.content)
    logger.info(f"Downloaded {cache_folder_name} to {cache_path}.")
    with ZipFile(total_cache_path, 'r') as zipObj:
        zipObj.extractall(cache_path)
    logger.info(f"Extracted {args.cache_folder_name} to {cache_path}.")
except Exception as e:
    logger.error(e)