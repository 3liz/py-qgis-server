#!/bin/bash

set -e

# Add /.local to path
export PATH=$PATH:/.local/bin

echo "-- HOME is $HOME"

echo "-- Installing required packages..."
pip3 install -q --prefer-binary --user -r requirements.pip
pip3 install -q --prefer-binary --user -r requirements.txt

pip3 install -q --user -e ./

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

# Disable qDebug stuff that bloats test outputs
export QT_LOGGING_RULES="*.debug=false;*.warning=false"

# Run new tests
cd tests/unittests && exec pytest -v $@

