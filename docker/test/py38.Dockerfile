FROM python:3.8.5-buster

ENV APP_NAME=congregate \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install jq curl -y

RUN pip install poetry

RUN wget https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN apt-get update -y && apt-get install -y powershell
