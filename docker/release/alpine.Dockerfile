FROM python:3.8.5-alpine

# Define the ENV variable
ENV CONGREGATE_PATH /opt/congregate

WORKDIR /opt/congregate

# Copy supervisor configuration
ADD congregate congregate
ADD frontend frontend
ADD dev/bin dev/bin
COPY congregate.sh pyproject.toml poetry.lock README.md package.json package-lock.json vue.config.js babel.config.js ./

# Installing required libraries
RUN apk upgrade && \
    apk add --no-cache bash less vim jq curl build-base openssl-dev libffi-dev libxml2 libxml2-dev libxslt libxslt-dev nodejs npm && \
    cd /opt/congregate && \
    cp congregate.sh /usr/local/bin/congregate && \
    pip install poetry

# RUN export PATH=$PATH:$HOME/.poetry/bin/poetry
RUN poetry install

# Initialize congregate directories
RUN congregate init

# Install Node
RUN npm install && \
    npm run build

RUN echo "alias ll='ls -al'" >> ~/.bashrc

EXPOSE 8000