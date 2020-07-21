FROM python:2.7.15-stretch

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install jq curl -y

RUN pip install poetry
