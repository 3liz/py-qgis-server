#!/bin/bash

set -e

pip3 install -U setuptools
pip3 install -U -r requirements.pip
pip3 install -U -r requirements.txt

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

python3 setup.py develop

# Run the server locally
qgisserver -b 127.0.0.1 -p 8080 --rootdir=$(pwd)/tests/data -w2 &>docker_test.log &

# Run new tests
cd tests && py.test -v

kill $(jobs -p)

