#!/usr/bin/env python3

import argparse
import logging, sys
from itertools import groupby
import json
import os
import re
import time

from str2bool import str2bool
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse

logging.basicConfig(
  stream=sys.stdout, 
  level=logging.INFO, 
  format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
  parser = argparse.ArgumentParser(description='Fetch file report and delete orphaned media assets from Immich.')
  parser.add_argument('--api_key', help='Immich API key for authentication', nargs='?', default=None)
  parser.add_argument('--api_url', help='Full address for Immich, including protocol and port', nargs='?', default=None)
  parser.add_argument('--skip_previous', help='Perform stacking only on photos that are not part of a stack. Much quicker.', nargs='?', default=True)
  parser.add_argument('--stack_method', help='JPGwithRAW, RAWwithJPG', nargs='?', default='JPGwithRAW')
  return parser.parse_args()

criteria_default = [
  {
    "key": "originalFileName",
    "split": {
      "key": ".",
      "index": 0
    }
  },
  {
    "key": "localDateTime"
  }
]

def get_criteria_config():
    criteria_override = os.environ.get("CRITERIA")
    if criteria_override:
        return json.loads(criteria_override)
    return criteria_default

def apply_criteria(x):
    criteria_list = []
    for item in get_criteria_config():
        value = x[item["key"]]
        if "split" in item.keys():
            split_key = item["split"]["key"]
            split_index = item["split"]["index"]
            value = value.split(split_key)[split_index]
        if "regex" in item.keys():
            regex_key = item["regex"]["key"]
            # expects at least one regex group to be defined
            regex_index = item["regex"].get("index", 1)
            match = re.match(regex_key, value)
            if match:
              value = match.group(regex_index)
            elif not str2bool(os.environ.get("SKIP_MATCH_MISS")):
              raise Exception(f"Match not found for value: {value}, regex: {regex_key}")
            else:
              return []
        criteria_list.append(value)
    return criteria_list

def parent_criteria(x):
  parent_ext = ['.jpg', '.jpeg', '.png']

  parent_promote = os.environ.get("PARENT_PROMOTE", "").split(",")
  parent_promote_baseline = 0

  lower_filename = x["originalFileName"].lower()

  if any(lower_filename.endswith(ext) for ext in parent_ext):
    parent_promote_baseline -= 100

  for key in parent_promote:
    if key.lower() in lower_filename:
      logger.info("promoting " + x["originalFileName"] + f" for key {key}")
      parent_promote_baseline -= 1

  return [parent_promote_baseline, x["originalFileName"]]


class Immich():
  def __init__(self, url: str, key: str):
    self.api_url = f'{urlparse(url).scheme}://{urlparse(url).netloc}/api'
    self.headers = {
      'x-api-key': key,
      'Accept': 'application/json'
    }
    self.assets = list()
    self.libraries = list()
  
  def fetchAssets(self, size: int = 1000) -> list:
    payload = {
      'size' : size,
      'page' : 1,
      #'withExif': True,
      'withStacked': True
    }
    assets_total = list()

    logger.info(f'⬇️  Fetching assets: ')
    logger.info(f'   Page size: {size}')

    while payload["page"] != None:

      session = Session()
      retry = Retry(connect=3, backoff_factor=0.5)
      adapter = HTTPAdapter(max_retries=retry)
      session.mount('http://', adapter)
      session.mount('https://', adapter)

      response = session.post(f"{self.api_url}/search/metadata", headers=self.headers, json=payload)

      if not response.ok:
        logger.error('   Error:', response.status_code, response.text)

      assets_total = assets_total + response.json()['assets']['items']
      payload["page"] = response.json()['assets']['nextPage']
    
    self.assets = assets_total
    
    logger.info(f'   Pages: {payload["page"]}')   
    logger.info(f'   Assets: {len(self.assets)}')
    
    return self.assets

  def fetchLibraries(self) -> list:
    logger.info('⬇️  Fetching libraries: ')

    session = Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    response = session.get(f"{self.api_url}/libraries", headers=self.headers)

    if not response.ok:
      logger.error('   Error:', response.status_code, response.text)

    self.libraries = response.json()

    for lib in self.libraries:
      logger.info(f'     {lib["id"]} {lib["name"]}')
    logger.info(f'   Libraries: {len(self.libraries)}')

    return self.libraries

  def removeOfflineFiles(self, library_id: str) -> None:
    session = Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    response = session.post(f"{self.api_url}/libraries/{library_id}/removeOffline", headers=self.headers)

    if response.ok:
      logger.info("  🟢 Success!")
    else:
      logger.error(f"  🔴 Error! {response.status_code} {response.text}") 

  def modifyAssets(self, payload: dict) -> None:
    session = Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    response = session.put(f"{self.api_url}/assets", headers=self.headers, json=payload)

    if response.ok:
      logger.info("  🟢 Success!")
    else:
      logger.error(f"  🔴 Error! {response.status_code} {response.text}") 


def stackBy(data: list, criteria) -> list:
  # Optional: remove incompatible file names
  if str2bool(os.environ.get("SKIP_MATCH_MISS")):
    data = filter(criteria, data)

  # Sort by primary and secondary criteria
  data = sorted(data, key=criteria)

  # Group by primary and secondary criteria
  groups = groupby(data, key=criteria)
  
  # Extract and process groups into a list of tuples
  groups = [(key, list(group)) for key, group in groups]
  
  # Filter only groups that have more than one item
  groups = [x for x in groups if len(x[1]) > 1 ] 

  return groups

def stratifyStack(stack: list) -> list:
  # Ensure the desired parent is first in the list
  return sorted(stack, key=parent_criteria)


def main():
  args = parse_arguments()

  # Prompt for admin API key if not provided
  api_key = args.api_key if args.api_key else input('Enter the Immich API key: ')

  # Prompt for Immich API address if not provided
  api_url = args.api_url if args.api_url else input('Enter the full web address for Immich, including protocol and port: ')

  if not api_key:
    print("API key is required")
    return
  if not api_url:
    print("API URL is required")
    return

  logger.info('============== INITIALIZING ==============')
  
  immich = Immich(api_url, api_key)
  
  data = immich.fetchAssets()

  stacks = stackBy(data, apply_criteria)

  for i, v in enumerate(stacks):
    key, stack = v

    stack = stratifyStack(stack)

    parent_id = stack[0]['id']
    children_id = []
    
    if args.skip_previous:
      children_id = [x['id'] for x in stack[1:] if x['stackCount'] == None ]
      
      if len(children_id) == 0:
        logger.info(f'{i}/{len(stacks)} Key: {key} SKIP! No new children!')
      
      else:
        logger.info(f'{i}/{len(stacks)} Key: {key}')
        logger.info(f'   Parent name: {stack[0]["originalFileName"]} ID: {parent_id}')
        for child in stack[1:]:
          logger.info(f'   Child name:  {child["originalFileName"]} ID: {child["id"]}')

    else:
      children_id = [x['id'] for x in stack[1:]]

      logger.info(f'{i}/{len(stacks)} Key: {key}')
      logger.info(f'   Parent name: {stack[0]["originalFileName"]} ID: {parent_id}')
      for child in stack[1:]:
        logger.info(f'   Child name:  {child["originalFileName"]} ID: {child["id"]}')

    if len(children_id) > 0:
      payload = {
        "ids": children_id,
        "stackParentId": parent_id
      }

      time.sleep(.1)
      immich.modifyAssets(payload)

if __name__ == '__main__':
  main()
