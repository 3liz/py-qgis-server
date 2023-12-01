#!/bin/bash

set -e

copy_qgis_configuration() {
    QGIS_CUSTOM_CONFIG_PATH=${QGIS_CUSTOM_CONFIG_PATH:-$QGIS_OPTIONS_PATH}
    if [[ -n $QGIS_CUSTOM_CONFIG_PATH ]]; then
        echo "Copying Qgis configuration: $QGIS_CUSTOM_CONFIG_PATH"
        cp -aRL $QGIS_CUSTOM_CONFIG_PATH/* $HOME/
    fi
    export QGIS_CUSTOM_CONFIG_PATH=$HOME
    export QGIS_OPTIONS_PATH=$HOME
}

[[ "$DEBUG_ENTRYPOINT" == "yes" ]]  && set -x

if [[ "$1" == "version" ]]; then
    version=`/opt/local/pyqgisserver/bin/pip list | grep py-qgis-server | tr -s [:blank:] | cut -d ' ' -f 2`
    qgis_version=`python3 -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION.split('-')[0])"`
    # Strip the 'rc' from the version
    # An 'rc' version is not released so as a docker image the rc is not relevant 
    # here
    echo "$qgis_version-${version%rc0}"
    exit 0
fi

# Check for uid (running with --user)
if [[ "$UID" != "0" ]]; then 
    QGSRV_USER=$UID:$(id -g)
else
    QGSRV_USER=${QGSRV_USER:-"9001:9001"}
fi

if [[ "$QGSRV_USER" =~ ^root:? ]] || [[ "$QGSRV_USER" =~ ^0:? ]]; then
    echo "QGSRV_USER must no be root !"
    exit 1 
fi

if [[ "$1" = "qgisserver-proxy" ]]; then
    shift
    echo "Running Qgis server proxy"
    exec gosu $QGSRV_USER qgisserver --proxy $@
fi 

# Qgis need a HOME
export HOME=/home/qgis

# Set the default QGSRV_CACHE_ROOTDIR
if [[ -z $QGSRV_CACHE_ROOTDIR ]]; then
    export QGSRV_CACHE_ROOTDIR=/qgis-data
    echo "QGSRV_CACHE_ROOTDIR set to $QGSRV_CACHE_ROOTDIR"
fi

if [ "$(id -u)" = '0' ]; then
    # Delete any actual Xvfb lock file
    # Because it can only be removed as root
    rm -rf /tmp/.X99-lock

    if [[ "$(stat -c '%u' $HOME)" == "0" ]] ; then
        chown $QGSRV_USER $HOME
        chmod 755 $HOME
    fi
    if [[ ! -e $QGSRV_CACHE_ROOTDIR ]]; then
        mkdir -p $QGSRV_CACHE_ROOTDIR
        chown $QGSRV_USER $QGSRV_CACHE_ROOTDIR
    fi
    exec gosu $QGSRV_USER  "$BASH_SOURCE" "$@"
fi

echo "Running as $QGSRV_USER"

if [[ "$(id -g)" == "0" ]]; then 
    echo "SECURITY WARNING: running as group 'root'"
fi

# Check if HOME is available
if [[ ! -d $HOME ]]; then
    echo "ERROR: Qgis require a HOME directory (default to $HOME)"
    echo "ERROR: You must mount the corresponding volume directory"
    exit 1
fi
# Check if HOME is writable
if [[ ! -w $HOME ]]; then
    echo "ERROR: $HOME must be writable for user:group $QGSRV_USER"
    echo "ERROR: You should consider the '--user' Docker option"
    exit 1
fi

# Check that QGSRV_CACHE_ROOTDIR exists and is readable
if [[ ! -r $QGSRV_CACHE_ROOTDIR ]]; then
    echo "ERROR: $QGSRV_CACHE_ROOTDIR do not exists or is not readable"
    exit 1
fi

# Check that QGSRV_CACHE_ROOTDIR is writable
if [[ ! -w $QGSRV_CACHE_ROOTDIR ]]; then
    echo "WARNING: $QGSRV_CACHE_ROOTDIR is not writable"
    echo "WARNING: this may lead to potential problems with gpkg datasets"
fi

QGSRV_DISPLAY_XVFB=${QGSRV_DISPLAY_XVFB:-ON}
#
# Set up xvfb
# https://www.x.org/archive/X11R7.6/doc/man/man1/Xvfb.1.xhtml
# see https://www.x.org/archive/X11R7.6/doc/man/man1/Xserver.1.xhtml
#
XVFB_DEFAULT_ARGS="-screen 0 1024x768x24 -ac +extension GLX +render -noreset"
XVFB_ARGS=${QGSRV_XVFB_ARGS:-":99 $XVFB_DEFAULT_ARGS"}

if [[ "$QGSRV_DISPLAY_XVFB" == "ON" ]]; then
 if [ -f /tmp/.X99-lock ]; then
     echo "ERROR: An existing lock file will prevent Xvfb to start"
     echo "If you expect restarting the container with '--user' option"
     echo "consider mounting /tmp with option '--tmpfs /tmp'"
     exit 1
 fi
    
 # RUN Xvfb in the background
 echo "Running Xvfb"
 nohup /usr/bin/Xvfb $XVFB_ARGS &
 export DISPLAY=":99"
fi

copy_qgis_configuration

# See https://github.com/qgis/QGIS/pull/5337
export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

# Make sure that QGSRV_SERVER_PLUGINPATH takes precedence over
# QGIS_PLUGINPATH
if [[ -n ${QGSRV_SERVER_PLUGINPATH} ]]; then
    export QGIS_PLUGINPATH=$QGSRV_SERVER_PLUGINPATH
fi

if [[ "$1" == "qgisserver-worker" ]]; then
    shift
    echo "Running Qgis server worker"
    exec qgisserver-worker --host=$ROUTER_HOST $@
else
    exec $@
fi

