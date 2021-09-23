FROM python:3.8.12-slim-buster

# Add ps-user and give them sudo privileges
RUN adduser ps-user && \
    usermod -aG sudo ps-user && \
    apt update && apt upgrade -y && apt install -y sudo && \
    sed -i 's/sudo.*ALL\=(ALL:ALL).*ALL/sudo ALL=(ALL) NOPASSWD:ALL/' /etc/sudoers

USER ps-user

RUN pip install --user poetry

USER root

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
COPY congregate.sh pyproject.toml poetry.lock README.md package.json package-lock.json vue.config.js babel.config.js .gitignore ./

# Set permissions for /data and /opt for ps-user
RUN chown ps-user:sudo /opt -R && \
    chmod 750 -R /opt

# Installing some basic utilities and updating apt
RUN apt-get update && \
    apt-get install less vim jq curl wget libcurl4 openssl liblzma5 screen git procps -y && \
    apt-get upgrade -y

# Install Node
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get install -y nodejs && \
    npm install --no-optional && \
    npm run build

# Install mongo
RUN mkdir /opt/mongo-install && \
    mkdir -p /var/lib/mongodb && \
    mkdir -p /var/log/mongodb && \
    mkdir -p /data/db && \
    chown ps-user: /var/lib/mongodb && \
    chown ps-user: /var/log/mongodb && \
    chown ps-user: /data -R && \
    cd /opt/mongo-install && \
    wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-debian10-4.4.4.tgz && \
    tar -zxvf mongodb-linux-*-4.4.4.tgz && \
    cp mongodb-linux-x86_64-debian10-4.4.4/bin/* /usr/local/bin/

RUN cd /opt/congregate && \
    chmod +x congregate && \
    ln congregate.sh /usr/bin/congregate

# Switch to ps-user
USER ps-user

# Install congregate
RUN cd /opt/congregate && \
    git init && \
    git add . && \
    git config --global user.email "migration@gitlab.com" && \
    git config --global user.name "congregate" && \
    git commit -m "Initial commit"
    
RUN export PATH=$PATH:$HOME/.local/bin && \
    echo "export PATH=$PATH" >> ~/.bashrc

RUN python3.8 -m poetry install

# Initialize congregate directories
RUN congregate init

run echo 'if [ -z "$(ps aux | grep mongo | grep -v grep)" ]; then mongod --fork --logpath /var/log/mongodb/mongod.log; fi' >> ~/.bashrc
RUN echo "alias ll='ls -al'" >> ~/.bashrc

RUN python3.8 -m poetry update

EXPOSE 8000
