FROM centos:centos8.4.2105

# Add ps-user and give them sudo privileges
RUN adduser ps-user && \
    gpasswd -a ps-user wheel && \
    yum update -y && yum install -y sudo && \
    sed -i 's/wheel.*ALL\=(ALL).*ALL/wheel ALL=(ALL) NOPASSWD:ALL/' /etc/sudoers

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
COPY congregate.sh pyproject.toml poetry.lock README.md package.json package-lock.json vue.config.js babel.config.js .gitignore LICENSE ./
COPY docker/release/centos/mongo_repo /etc/yum.repos.d/mongodb-org-4.4.repo

RUN mkdir -p /data/db

# Set /data and /opt folder permissions for ps-user
RUN chown -R ps-user:wheel /data && \
    chmod -R 750 /data && \
    chown -R ps-user:wheel /opt && \
    chmod -R 750 /opt

# Installing yum-installable libraries
RUN yum update -y && \
    yum install -y less vim jq curl git mongodb-org-4.4.4 mongodb-org-server-4.4.4 mongodb-org-shell-4.4.4 mongodb-org-mongos-4.4.4 mongodb-org-tools-4.4.4 \
    gcc openssl-devel bzip2-devel libffi-devel zlib-devel make epel-release xz-devel && \
    yum install -y screen

# Install Python
RUN cd /opt && \
    curl https://www.python.org/ftp/python/3.8.12/Python-3.8.12.tgz -o Python-3.8.12.tgz && \
    tar xzf Python-3.8.12.tgz && \
    cd Python-3.8.12 && \
    ./configure --enable-optimizations && \
    sudo make altinstall && \
    cd /opt && \
    rm Python-3.8.12.tgz && \
    rm -r Python-3.8.12

# The alias takes precendence once you are in an interactive shell (-it)
# in Docker, so this "fixes" the build steps afterwards, but doesn't seem to
# break anything else
RUN echo -e '#!/bin/bash\npython3.8 "$@"' > /usr/local/sbin/python && \
    chmod +x /usr/local/sbin/python

# Install Node
RUN curl -sL https://rpm.nodesource.com/setup_12.x | bash - && \
    yum install -y nodejs

# Set dist/ folder permissions for ps-user
RUN chown -R ps-user:wheel dist && \
    chmod -R 750 dist

# Create python symlinks
RUN rm -f /usr/bin/python3 && \
    cd /usr/bin && \
    ln -s python3.8 python3 && \
    rm /usr/local/sbin/python

# Set permissions to execute the congregate command
RUN cd /opt/congregate && \
    chmod +x congregate.sh && \
    ln congregate.sh /usr/bin/congregate 

# Switch to ps-user for the rest of the installation
USER ps-user

# Set up the bashrc
RUN echo 'if [ -z "$(ps aux | grep mongo | grep -v grep)" ]; then sudo mongod --fork --logpath /var/log/mongodb/mongod.log; fi' >> ~/.bashrc
RUN echo "alias python='python3.8'" >> ~/.bashrc
RUN echo "alias python3='python3.8'" >> ~/.bashrc
RUN echo "alias pip='python3.8 -m pip'" >> ~/.bashrc
RUN echo "alias ll='ls -al'" >> ~/.bashrc
RUN echo "alias license='cat /opt/congregate/LICENSE'" >> ~/.bashrc

RUN echo "CHECKING PYTHON VERSION" && \
    python3.8 -V

# Install congregate
RUN cd /opt/congregate && \
    git init && \
    git add . && \
    git config --global user.email "migration@gitlab.com" && \
    git config --global user.name "congregate" && \
    git commit -m "Initial commit" && \
    python3.8 -m pip install --user poetry && \
    python3.8 -m poetry install

# Initialize congregate directories
RUN congregate init

# Install node dependencies
RUN npm install --no-optional && \
    npm run build

EXPOSE 8000
