FROM rockylinux/rockylinux:8.5

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
COPY congregate.sh pyproject.toml poetry.lock README.md .gitignore LICENSE ./

RUN mkdir -p /data/db

# Set /data and /opt folder permissions for ps-user
RUN chown -R ps-user:wheel /data && \
    chmod -R 750 /data && \
    chown -R ps-user:wheel /opt && \
    chmod -R 750 /opt

# Installing yum-installable libraries
RUN yum update -y && \
    yum install -y less vim jq curl git  \
    gcc openssl-devel bzip2-devel libffi-devel zlib-devel make epel-release xz-devel util-linux-user sqlite-devel && \
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
RUN curl -sL https://rpm.nodesource.com/setup_16.x | bash - && \
    yum install -y nodejs

# Create python symlinks
RUN rm -f /usr/bin/python3 && \
    cd /usr/bin && \
    ln -s python3.8 python3 && \
    rm /usr/local/sbin/python

# Set permissions to execute the congregate command
RUN cd /opt/congregate && \
    chmod +x congregate.sh && \
    ln congregate.sh /usr/bin/congregate 

# Install zsh
RUN yum install -y zsh && chsh -s /usr/bin/zsh && chsh -s /usr/bin/zsh ps-user

# Switch to ps-user for the rest of the installation
USER ps-user

# Install oh-my-zsh
RUN sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

RUN export PATH=$PATH:$HOME/.local/bin && \
    echo "export PATH=$PATH" >> ~/.bashrc && \
    echo "export PATH=$PATH" >> ~/.zshrc

# Set up the bashrc
RUN echo "alias python='python3.8'" >> ~/.bashrc && \
    echo "alias python='python3.8'" >> ~/.zshrc
RUN echo "alias python3='python3.8'" >> ~/.bashrc && \
    echo "alias python3='python3.8'" >> ~/.zshrc
RUN echo "alias pip='python3.8 -m pip'" >> ~/.bashrc && \
    echo "alias pip='python3.8 -m pip'" >> ~/.zshrc
RUN echo "alias ll='ls -al'" >> ~/.bashrc && \
    echo "alias ll='ls -al'" >> ~/.zshrc
RUN echo "alias license='cat /opt/congregate/LICENSE'" >> ~/.bashrc && \
    echo "alias license='cat /opt/congregate/LICENSE'" >> ~/.zshrc


RUN echo "CHECKING PYTHON VERSION" && \
    python3.8 -V

# Install congregate
RUN cd /opt/congregate && \
    git init && \
    git add . && \
    git config --global user.email "migration@gitlab.com" && \
    git config --global user.name "congregate" && \
    git commit -m "Initial commit"

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3.8 - && \
    export PATH="/home/ps-user/.local/bin:$PATH" && \
    poetry --version && \
    poetry install

# Install node dependencies
RUN cd frontend && \
    npm install && \
    npm run build

USER root

# Set dist/ folder permissions for ps-user
RUN cd /opt/congregate && \
    chown -R ps-user:wheel dist && \
    chmod -R 750 dist

USER ps-user

# Initialize congregate directories
WORKDIR /opt/congregate
RUN export PATH=$PATH:/home/ps-user/.local/bin/ && ./congregate.sh init

EXPOSE 8000
