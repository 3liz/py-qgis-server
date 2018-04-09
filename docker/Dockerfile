FROM python:3.6-alpine3.6
MAINTAINER David Marteau <david.marteau@3liz.com>

RUN apk --no-cache add zeromq && \
    pip install --no-index --find-links=/wheels pyzmq

