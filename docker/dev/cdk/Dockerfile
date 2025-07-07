FROM python:3.10.18-slim-bookworm

ENV APP_NAME=congregate \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install jq curl wget git build-essential -y

# Install NVM to manage node versions
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Update Pip and install Poetry
RUN pip install --upgrade pip
RUN pip install poetry

