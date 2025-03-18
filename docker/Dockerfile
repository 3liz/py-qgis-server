# syntax=docker/dockerfile:1
# vim: ft=dockerfile
ARG REGISTRY_PREFIX=''
ARG QGIS_VERSION=release

FROM  ${REGISTRY_PREFIX}qgis-platform:${QGIS_VERSION} AS base

LABEL Description="QGIS3 Python Server" Vendor="3liz.org"
LABEL Maintainer="David Marteau <david.marteau@3liz.com>"

ARG PIP_OPTIONS

# Setup will use this variable for copying manifest
ENV QGSRV_DATA_PATH=/usr/local/share/qgis-server


# Install qgis-plugin-manager
RUN --mount=type=cache,target=/.python-cache mkdir -p /opt/local/ \
    && python3 -m venv --system-site-packages /opt/local/plugin-manager \
    && cd /usr/local/bin \
    && /opt/local/plugin-manager/bin/pip install -U --upgrade-strategy=eager \
        --cache-dir=/.python-cache pip setuptools wheel packaging>=22.0 \
    && /opt/local/plugin-manager/bin/pip install -U --upgrade-strategy=eager \
         --cache-dir=/.python-cache qgis-plugin-manager \
    && cd /usr/local/bin \
    && echo "#!/bin/bash" > qgis-plugin-manager \
    && echo "export QGIS_PLUGINPATH=\${QGIS_PLUGINPATH:-\$QGSRV_SERVER_PLUGINPATH}" >> qgis-plugin-manager \
    && echo "echo \"QGIS_PLUGINPATH set to \$QGIS_PLUGINPATH\"" >> qgis-plugin-manager \
    && echo "/opt/local/plugin-manager/bin/qgis-plugin-manager \"\$@\"" >> qgis-plugin-manager \
    && chmod 755 qgis-plugin-manager \
    ${NULL}


COPY pyqgisserver py-qgis-server/pyqgisserver
COPY pyqgisservercontrib py-qgis-server/pyqgisservercontrib
COPY pyproject.toml VERSION py-qgis-server/

# Create virtualenv for installing server
RUN --mount=type=cache,target=/.python-cache mkdir -p /opt/local/ \
    && python3 -m venv --system-site-packages /opt/local/pyqgisserver \
    && cd /usr/local/bin \
    && /opt/local/pyqgisserver/bin/pip install -U \
        --cache-dir=/.python-cache pip setuptools wheel \
        --upgrade-strategy=eager \
    && /opt/local/pyqgisserver/bin/pip install -U --cache-dir=/.python-cache \
        --upgrade-strategy=eager \
        -e /py-qgis-server \
    && ln -s /opt/local/pyqgisserver/bin/qgisserver \
    && ln -s /opt/local/pyqgisserver/bin/qgisserver-worker \
    ${NULL}

COPY docker/docker-entrypoint.sh /
RUN chmod 0755 /docker-entrypoint.sh && mkdir -p /home/qgis && chmod 777 /home/qgis

# Set uid root on Xvfb
# Allow us to run Xvfb when the container runs with '-u' option
RUN chmod u+s /usr/bin/Xvfb

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["qgisserver"]

# ============
# AMQP support
# ============
FROM base AS amqp

ARG PIP_OPTIONS

RUN /opt/local/pyqgisserver/bin/pip install --no-cache-dir $PIP_OPTIONS  "py-amqp-client<=2.0.0"
