#!/bin/bash

set -e

# Add /.local to path
export PATH=$PATH:/.local/bin

PIP="pip3 install -U --user --no-cache"

$PIP setuptools
$PIP --prefer-binary -r requirements.txt

pip3 install --user --no-cache -e ./

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

if [ -e /amqp_src ]; then
    pip3 install --user --no-cache -e /amqp_src/
fi

# Run the server locally
echo "Running server..."
qgisserver -b 0.0.0.0 -p 8080 -c /server.conf



