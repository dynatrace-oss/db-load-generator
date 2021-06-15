FROM python:latest AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-11-jre-headless \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/* \
    && pip install db-load-generator[dramatiq]

ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64

WORKDIR /dbload

ENTRYPOINT [ "dbload" ]
