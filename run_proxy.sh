#!/bin/sh

set -e

PIP="pip3 install -U --user --no-index --find-links=/wheels"

$PIP setuptools
$PIP -r requirements.pip
$PIP -r requirements.txt

pip install --user -e ./

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

# Add /.local to path
export PATH=$PATH:/.local/bin

# Run the server locally
echo "Running server proxy..."
qgisserver -b 0.0.0.0 -p 8080 --proxy --rootdir=$(pwd)/tests/data -w1



