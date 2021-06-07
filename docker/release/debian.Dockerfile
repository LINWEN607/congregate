FROM python:3.8.10-slim-buster

# Define the ENV variable
ENV CONGREGATE_PATH=/opt/congregate \
    APP_PATH=/opt/congregate \
    APP_NAME=congregate \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /opt/congregate

# Copy supervisor configuration
ADD congregate congregate
ADD frontend frontend
ADD dev/bin dev/bin
COPY congregate.sh pyproject.toml poetry.lock README.md package.json package-lock.json vue.config.js babel.config.js ./

# Installing some basic utilities and updating apt
RUN apt-get update && \
    apt-get install less vim jq curl wget libcurl4 openssl liblzma5 screen git -y && \
    apt-get upgrade -y


# Install mongo
RUN mkdir /mongo-install && \
    mkdir -p /var/lib/mongodb && \
    mkdir -p /var/log/mongodb && \
    mkdir -p /data/db && \
    chown `whoami` /var/lib/mongodb && \
    chown `whoami` /var/log/mongodb && \
    cd /mongo-install && \
    wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-debian10-4.4.4.tgz && \
    tar -zxvf mongodb-linux-*-4.4.4.tgz && \
    cp mongodb-linux-x86_64-debian10-4.4.4/bin/* /usr/local/bin/

# Install congregate
RUN cd /opt/congregate && \
    chmod +x congregate && \
    cp congregate.sh /usr/local/bin/congregate && \
    git init && \
    git add . && \
    git config --global user.email "migration@gitlab.com" && \
    git config --global user.name "congregate" && \
    git commit -m "Initial commit" && \
    pip install poetry

# RUN export PATH=$PATH:$HOME/.poetry/bin/poetry
RUN poetry install

# Initialize congregate directories
RUN congregate init

# Install Node
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get install -y nodejs && \
    npm install --no-optional && \
    npm run build

run echo 'if [ -z "$(ps aux | grep mongo | grep -v grep)" ]; then mongod --fork --logpath /var/log/mongodb/mongod.log; fi' >> ~/.bashrc
RUN echo "alias ll='ls -al'" >> ~/.bashrc

EXPOSE 8000
