#!/bin/bash

set -e

echo "-- HOME is $HOME"

VENV_PATH=/.local/venv

PIP="$VENV_PATH/bin/pip"
PIP_INSTALL="$VENV_PATH/bin/pip install -U"

echo "-- Creating virtualenv"
python3 -m venv --system-site-packages $VENV_PATH

echo "-- Installing required packages..."
$PIP_INSTALL -q pip setuptools wheel
$PIP_INSTALL -q --prefer-binary -r requirements.pip
$PIP_INSTALL -q --prefer-binary -r requirements.txt

$PIP install -e ./

if [ -e /amqp_src ]; then
    $PIP install -e /amqp_src/
fi

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

# Disable qDebug stuff that bloats test outputs
export QT_LOGGING_RULES="*.debug=false;*.warning=false"

export QGSRV_SERVER_HTTP_PROXY=yes

# Run new tests
cd tests/unittests && exec $VENV_PATH/bin/pytest -v $@

