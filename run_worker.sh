#!/bin/sh

set -e

PIP="pip3 install -U --user"

$PIP setuptools
$PIP -r requirements.pip
$PIP -r requirements.txt

pip3 install --user -e ./

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

# Add /.local to path
export PATH=$PATH:/.local/bin

# Run the server locally
echo "Running worker..."
qgisserver-worker --rootdir=$(pwd)/tests/data --host=$ROUTER_HOST



