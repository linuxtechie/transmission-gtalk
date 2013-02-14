#!/bin/sh
trap "" 1
logfile=/tmp/dockstar-gtalk.debug.$$.txt
exec > $logfile 2>&1
set -x
cd /opt/dockstarmailer/dockstar-gtalk
export PYTHONPATH=/opt/dockstarmailer/dockstar-gtalk:/opt/dockstarmailer/dockstar-gtalk/err
python err/scripts/err.py -c . -d
