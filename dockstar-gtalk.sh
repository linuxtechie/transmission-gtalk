#!/bin/sh
trap "" 1
logfile=/tmp/dockstar-gtalk.debug.$$.txt
exec > $logfile 2>&1
set -x
PARENT_DIR=$(pwd)
echo $PARENT_DIR
export PYTHONPATH=${PARENT_DIR}:${PARENT_DIR}/err
python err/scripts/err.py -c .  -d
