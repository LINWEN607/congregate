FROM python:3.8.5-buster

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install jq curl -y

RUN pip install poetry

