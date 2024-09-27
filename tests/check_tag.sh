#!/bin/bash

VERSION=$1
METADATA=$(cat config.mk | grep "VERSION:=" |  cut -d '=' -f2)

if [ "$METADATA" != "$VERSION" ];
then
    echo "The Makefile file has ${METADATA} while the requested tag is ${VERSION}."
    echo "Aborting"
    exit 1
fi

echo "The Makefile is synced with ${VERSION}"
exit 0
