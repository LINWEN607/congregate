FROM python:3.8.12-slim-buster

ENV APP_NAME=congregate \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install jq curl wget git build-essential -y

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3.8 - && \
    export PATH="/root/.local/bin:$PATH" && \
    poetry --version

RUN wget https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN apt-get update -y && apt-get install -y powershell
