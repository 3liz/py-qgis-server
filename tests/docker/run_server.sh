#!/bin/bash

set -e

PIP="pip3 install -U --user"

$PIP setuptools
$PIP --prefer-binary -r requirements.txt

pip3 install --user -e ./

export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

# Add /.local to path
export PATH=$PATH:/.local/bin

if [ -e /amqp_src ]; then
    pip3 install --user -e /amqp_src/
fi

# Run the server locally
echo "Running server..."
qgisserver -b 0.0.0.0 -p 8080 -c /server.conf



