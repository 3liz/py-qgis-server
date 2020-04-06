ARG REGISTRY_PREFIX=''
ARG QGIS_VERSION=latest

FROM  ${REGISTRY_PREFIX}qgis-platform:${QGIS_VERSION}
MAINTAINER David Marteau <david.marteau@3liz.com>
LABEL Description="QGIS3 Python Server" Vendor="3liz.org"

ARG SERVER_VERSION

RUN apt-get update && apt-get install -y --no-install-recommends gosu \
    && apt-get clean  && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/man

ENV QGSRV_DATA_PATH=/usr/local/share/qgis-server

# Install server
COPY dist/py-qgis-wps-$SERVER_VERSION.tar.gz /
RUN pip3 install --no-cache-dir /py-qgis-wps-$WPS_VERSION.tar.gz

COPY /docker-entrypoint.sh /
RUN chmod 0755 /docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]


