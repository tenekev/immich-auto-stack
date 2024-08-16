#!/usr/bin/env python3

import argparse
import logging, sys
from itertools import groupby
import time

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
  # Sort by primary and secondary criteria
  data.sort(key=criteria)

  # Group by primary and secondary criteria
  groups = groupby(data, key=criteria)
  
  # Extract and process groups into a list of tuples
  groups = [(key, list(group)) for key, group in groups]
  
  # Filter only groups that have more than one item
  groups = [x for x in groups if len(x[1]) > 1 ] 

  return groups

def stratifyStack(stack: list) -> list:
  parent_ext = ['.jpg', '.jpeg', '.png']
  parent_ext2 = ['.3fr', '.ari', '.arw', '.bay', '.braw', '.crw', '.cr2', '.cr3', '.cap', '.data', '.dcs', '.dcr', '.dng', '.drf', '.eip', '.erf', '.fff', '.gpr', '.iiq', '.k25', '.kdc', '.mdc', '.mef', '.mos', '.mrw', '.nef', '.nrw', '.obm', '.orf', '.pef', '.ptx', '.pxn', '.r3d', '.raf', '.raw', '.rwl', '.rw2', '.rwz', '.sr2', '.srf', '.srw', '.tif', '.x3f']
  parents = []
  children = []
  
  for asset in stack:
    if any(asset['originalFileName'].lower().endswith(ext) for ext in parent_ext):
      parents.append(asset)
    else:
      children.append(asset)

  return parents + children


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

  criteria = lambda x: (
    x['originalFileName'].split('.')[0], 
    x['localDateTime']
  )
  stacks = stackBy(data, criteria)

  for i, v in enumerate(stacks):
    key, stack = v

    stack = stratifyStack(stack)

    parent_id = stack[0]['id']
    children_id = []
    
    if args.skip_previous:
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

      time.sleep(.1)
      immich.modifyAssets(payload)

if __name__ == '__main__':
  main()