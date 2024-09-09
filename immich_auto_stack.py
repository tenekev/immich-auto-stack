#!/usr/bin/env python3

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

def apply_criteria(x: dict) -> list:
    """
    Given a photo dataset, pick out the identified keys as defined by CRITERIA.

    Keys can be raw values or a subset of values (using split or regex modifiers).

    If any of the key values is abnormal (None, absent, regex mismatch), return
    an empty list.
    """
    criteria_list = []
    for item in get_criteria_config():
        value = x.get(item["key"])
        if value is None:
            # None is a undesireable key value for this project because we rely on keys
            # to categorize similar photos, and typically None represents the absence
            # of information.
            #
            # A real scenario example: suppose some photos have not yet generated
            # thumbnails. It would be undesireable to create a stack of all the photos
            # whose thumbhash is None.
            return []
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

  parent_promote = list(filter(None, os.environ.get("PARENT_PROMOTE", "").split(",")))
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

    session = Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    while payload["page"] != None:
      response = session.post(f"{self.api_url}/search/metadata", headers=self.headers, json=payload)

      if not response.ok:
        logger.error('   Error:', response.status_code, response.text)

      response_data = response.json()
      assets_total = assets_total + response_data['assets']['items']
      payload["page"] = response_data['assets']['nextPage']
    
    self.assets = assets_total
    
    logger.info(f'   Pages: {payload["page"]}')   
    logger.info(f'   Assets: {len(self.assets)}')
    
    return self.assets

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

  # Raise error if any groups have an empty key
  if any((group[0] == [] or None in group[0]) for group in groups):
      raise Exception(
          "Some photos do not match the criteria you provided. Consider refining your"
          "criteria. If the criteria was not intended to match all files, use the"
          "SKIP_MATCH_MISS environment variable to skip processing of those photos."
      )

  return groups

def stratifyStack(stack: list) -> list:
  # Ensure the desired parent is first in the list
  return sorted(stack, key=parent_criteria)


def main():

  api_key = os.environ.get("API_KEY", False)

  api_url = os.environ.get("API_URL", "http://immich_server:3001/api")

  skip_previous = str2bool(os.environ.get("SKIP_PREVIOUS", True))

  dry_run = str2bool(os.environ.get("DRY_RUN", False))

  if not api_key:
    logger.warn("API key is required")
    return

  logger.info('============== INITIALIZING ==============')

  if dry_run:
    logger.info('🔒  Dry run enabled, no changes will be applied')
  
  immich = Immich(api_url, api_key)
  
  assets = immich.fetchAssets()

  stacks = stackBy(assets, apply_criteria)

  for i, v in enumerate(stacks):
    key, stack = v

    stack = stratifyStack(stack)

    parent_id = stack[0]['id']
    children_id = []
    
    if skip_previous:
      children_id = [x['id'] for x in stack[1:] if x['stackCount'] == None ]
      
      if len(children_id) == 0:
        logger.info(f'{i}/{len(stacks)} Key: {key} SKIP! No new children!')
        continue
      
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

      if not dry_run:
        time.sleep(.1)
        immich.modifyAssets(payload)

if __name__ == '__main__':
  main()
