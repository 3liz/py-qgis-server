# syntax=docker/dockerfile:1
# vim: ft=dockerfile
ARG REGISTRY_PREFIX=''
ARG QGIS_VERSION=latest

FROM  ${REGISTRY_PREFIX}qgis-platform:${QGIS_VERSION}
MAINTAINER David Marteau <david.marteau@3liz.com>
LABEL Description="QGIS3 Python Server" Vendor="3liz.org"

ARG PIP_OPTIONS
ARG BUILD_VERSION

# Setup will use this variable for copying manifest
ENV QGSRV_DATA_PATH=/usr/local/share/qgis-server

# Create virtualenv for installing server
RUN mkdir -p /opt/local/ \ 
    && python3 -m venv --system-site-packages /opt/local/pyqgisserver && cd /usr/local/bin \
    && /opt/local/pyqgisserver/bin/pip install -U --no-cache-dir pip setuptools wheel \
    && /opt/local/pyqgisserver/bin/pip install --no-cache-dir $PIP_OPTIONS   \
        "py-qgis-server==${BUILD_VERSION}" \
        "py-amqp-client<=2.0.0" \
        qgis-plugin-manager \
    && ln -s /opt/local/pyqgisserver/bin/qgisserver \
    && ln -s /opt/local/pyqgisserver/bin/qgisserver-worker \
    && echo "#!/bin/bash" > qgis-plugin-manager \
    && echo "export QGIS_PLUGINPATH=\${QGIS_PLUGINPATH:-\$QGSRV_SERVER_PLUGINPATH}" >> qgis-plugin-manager \
    && echo "echo \"QGIS_PLUGINPATH set to \$QGIS_PLUGINPATH\"" >> qgis-plugin-manager \
    && echo "/opt/local/pyqgisserver/bin/qgis-plugin-manager \"\$@\"" >> qgis-plugin-manager \
    && chmod 755 qgis-plugin-manager \
    && rm -rf /root/.cache /root/.ccache

COPY docker-entrypoint.sh /
RUN chmod 0755 /docker-entrypoint.sh && mkdir -p /home/qgis && chmod 777 /home/qgis

# Set uid root on Xvfb
# Allow us to run Xvfb when the container runs with '-u' option
RUN chmod u+s /usr/bin/Xvfb

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD ["qgisserver"]
