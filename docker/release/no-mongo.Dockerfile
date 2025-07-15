FROM rockylinux/rockylinux:8.10

# Add ps-user and give them sudo privileges
RUN adduser ps-user && \
    gpasswd -a ps-user wheel && \
    yum update -y && yum install -y sudo && \
    sed -i 's/wheel.*ALL\=(ALL).*ALL/wheel ALL=(ALL) NOPASSWD:ALL/' /etc/sudoers
    
# Define the ENV variable
ENV CONGREGATE_PATH=/opt/congregate \
    APP_PATH=/opt/congregate \
    APP_NAME=congregate \
    PIP_DEFAULT_TIMEOUT=300 \
    PATH=/home/ps-user/bin:/home/ps-user/.local/bin:/home/ps-user/.nvm:/home/ps-user/.pyenv/bin:/home/ps-user/.pyenv/shims:/usr/local/sbin:/usr/local/bin:$PATH

WORKDIR /opt/congregate

ADD congregate congregate
ADD frontend frontend
ADD dev/bin dev/bin
COPY congregate.sh pyproject.toml poetry.lock README.md .gitignore LICENSE ./

# Set /data and /opt folder permissions for ps-user
RUN chown -R ps-user:wheel /opt && \
    chmod -R 750 /opt

# Installing yum-installable libraries
RUN yum update -y && \
    yum install -y less vim jq curl git findutils readline ncurses ncurses-libs \
    gcc openssl-devel bzip2-devel libffi-devel zlib-devel make \
    epel-release xz-devel util-linux-user sqlite-devel procps && \
    yum install -y screen && \
    crb enable


# Install zsh
RUN yum install -y zsh && chsh -s /usr/bin/zsh && chsh -s /usr/bin/zsh ps-user

USER ps-user

# Install NVM, NPM, and Node
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash && \
    export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")" && \
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && \
    cd /opt/congregate/frontend && \
    nvm install && \
    npm install && \
    npm run build

# Install Python through pyenv
RUN curl https://pyenv.run | bash && \
    [[ -d $PYENV_ROOT/bin ]] && \
    eval "$(pyenv init -)" && \
    pyenv install 3.10 && \
    pyenv global 3.10

# Install oh-my-zsh
RUN sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

RUN echo "alias ll='ls -al'" >> ~/.bashrc && \
    echo "alias ll='ls -al'" >> ~/.zshrc
RUN echo "alias license='cat /opt/congregate/LICENSE'" >> ~/.bashrc && \
    echo "alias license='cat /opt/congregate/LICENSE'" >> ~/.zshrc
RUN echo "export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"" >> ~/.zshrc && \
    echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.zshrc

RUN echo "CHECKING PYTHON VERSION" && \
    python3 -V

# Install congregate
RUN cd /opt/congregate && \
    git init && \
    git add . && \
    git config --global user.email "migration@gitlab.com" && \
    git config --global user.name "congregate" && \
    git commit -m "Initial commit"

# Install poetry
RUN python -m pip install --user poetry==1.8.5 setuptools==80.9.0 && \
    python3.10 -m poetry --version && \
    poetry --version && \
    poetry install

USER root

# Set dist/ folder permissions for ps-user
RUN cd /opt/congregate && \
    chown -R ps-user:wheel dist && \
    chmod -R 750 dist

# Supervisor setup
RUN pip3 install supervisor && \
    mkdir -p /etc/supervisor/conf.d/ && \
    mkdir -p /var/log/supervisord/ && \
    chown -R ps-user: /var/log/supervisord

RUN chmod +x congregate.sh && ln -s /opt/congregate/congregate.sh /home/ps-user/.local/bin/congregate

COPY docker/release/centos/*.conf /etc/supervisor/conf.d/

RUN usermod -a -G render ps-user

USER ps-user

# Initialize congregate directories
WORKDIR /opt/congregate
RUN congregate init

EXPOSE 8000
EXPOSE 5555
