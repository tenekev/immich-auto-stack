#!/usr/bin/env sh

args="--api_key $API_KEY --api_url $API_URL"

if [ ! -z "$SKIP_PREVIOUS" ]; then
    args="--skip_previous $SKIP_PREVIOUS $args"
fi

BASEDIR=$(dirname "$0")
echo $args | xargs python3 -u $BASEDIR/immich_auto_stack.py