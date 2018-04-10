#!/bin/sh

# This scripts is expected to be run in an python:3.6 alpine with zmq
# installed and python requirements available as precompiled wheels.

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
echo "Running server..."
qgisserver -b 0.0.0.0 -p 8080 --proxy -j1



