#!/usr/bin/env sh

args="--api_key $API_KEY --api_url $API_URL --skip_previous $SKIP_PREVIOUS"

BASEDIR=$(dirname "$0")
echo $args | xargs python3 -u $BASEDIR/immich_auto_stack.py