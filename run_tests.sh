#!/bin/bash

set -e

pip3 install -U --user setuptools
pip3 install -U --user -r requirements.pip
pip3 install -U --user -r requirements.txt

pip3 install --user -e ./

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

# Add /.local to path
export PATH=$PATH:/.local/bin

export QGSRV_LOGGING_LEVEL=DEBUG

# Run the server locally
echo "Running server..."
qgisserver -b 127.0.0.1 -p 8080 --timeout=3 --rootdir=$(pwd)/tests/data -w1 &>docker-test.log &

# Wait for server to start
sleep 5
# Run new tests
#echo "Launching test"
cd tests && py.test -v
kill $(jobs -p)

