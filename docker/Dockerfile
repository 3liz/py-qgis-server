ARG REGISTRY_PREFIX=''
ARG QGIS_VERSION=latest

FROM  ${REGISTRY_PREFIX}qgis-platform:${QGIS_VERSION}
MAINTAINER David Marteau <david.marteau@3liz.com>
LABEL Description="QGIS3 Python Server" Vendor="3liz.org"

ARG git_branch=master
ARG git_repository=https://github.com/3liz/py-qgis-server.git

RUN apt-get update && apt-get install -y --no-install-recommends gosu git make \
    && apt-get clean  && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/man

ENV QGSRV_DATA_PATH=/usr/local/share/qgis-server

# Install server
RUN git clone --branch $git_branch --depth=1 $git_repository py-qgis-server \
    && make -C py-qgis-server dist \
    && pip3 install py-qgis-server/build/dist/*.tar.gz \
    && rm -rf py-qgis-server \
    && rm -rf /root/.cache /root/.ccache

COPY /docker-entrypoint.sh /
RUN chmod 0755 /docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]


