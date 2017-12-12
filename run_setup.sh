#!/bin/bash

set -e

# Uninstall this in order to get
# latest commit
pip3 uninstall -y qgis-python-tools

pip3 install -U --user setuptools
pip3 install -U --user -r requirements.pip
pip3 install -U --user -r requirements.txt

pip3 install --user -e ./

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

# Add /.local to path
export PATH=$PATH:/.local/bin

# Run the server locally
echo "Running server..."
qgisserver -b 0.0.0.0 -p 8080 --rootdir=$(pwd)/tests/data -w1



