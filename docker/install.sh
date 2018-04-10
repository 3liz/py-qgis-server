#!/bin/sh

apk --no-cache add zeromq
pip install -U --no-index --find-links=/.wheels -r requirements.txt

