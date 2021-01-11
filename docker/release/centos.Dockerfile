from centos:centos8

# Define the ENV variable
ENV CONGREGATE_PATH=/opt/congregate \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /opt/congregate

# Copy supervisor configuration
ADD congregate congregate
ADD frontend frontend
ADD dev/bin dev/bin
COPY congregate.sh pyproject.toml poetry.lock README.md package.json package-lock.json vue.config.js babel.config.js .gitignore ./
COPY docker/release/centos/mongo_repo /etc/yum.repos.d/mongodb-org-4.4.repo

RUN mkdir -p /data/db

# Installing some basic utilities and updating apt
RUN yum update -y && \
    yum install -y less vim jq curl git mongodb-org-4.4.1 mongodb-org-server-4.4.1 mongodb-org-shell-4.4.1 mongodb-org-mongos-4.4.1 mongodb-org-tools-4.4.1 python3.8 epel-release && \
    yum install -y screen && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3 get-pip.py

run echo 'if [ -z "$(ps aux | grep mongo | grep -v grep)" ]; then mongod --fork --logpath /var/log/mongodb/mongod.log; fi' >> ~/.bashrc
RUN echo "alias python='python3.8'" >> ~/.bashrc
RUN echo "alias python3='python3.8'" >> ~/.bashrc

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
RUN curl -sL https://rpm.nodesource.com/setup_12.x | bash - && \
    yum install -y nodejs && \
    npm install --no-optional && \
    npm run build

RUN echo "alias ll='ls -al'" >> ~/.bashrc

RUN rm -f /usr/bin/python3 && \
    cd /usr/bin && \
    ln -s python3.8 python3

EXPOSE 8000
