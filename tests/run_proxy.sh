#!/bin/bash

set -e

VENV_PATH=/.local/venv

PIP="$VENV_PATH/bin/pip"
PIP_INSTALL="$VENV_PATH/bin/pip install -U"

echo "-- Creating virtualenv"
python3 -m venv --system-site-packages $VENV_PATH

echo "-- Installing required packages..."
$PIP_INSTALL -q pip setuptools wheel
$PIP install -e ./

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

if [ -e /amqp_src ]; then
    $PIP install -e /amqp_src/
fi

# Run the server locally
echo "Running server..."
exec $VENV_PATH/bin/qgisserver -b 0.0.0.0 -p 8080 --proxy



