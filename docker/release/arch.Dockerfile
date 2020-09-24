FROM archlinux:20200908

# Define the ENV variable
ENV CONGREGATE_PATH /opt/congregate

WORKDIR /opt/congregate

# Copy supervisor configuration
ADD congregate congregate
ADD frontend frontend
ADD dev/bin dev/bin
COPY congregate.sh pyproject.toml poetry.lock README.md package.json package-lock.json vue.config.js babel.config.js ./

# Installing some basic utilities and updating apt
RUN pacman -Sy && \
    pacman -S --noconfirm python python-pip less vim jq curl nodejs-lts-erbium npm

# TODO: DB integration

# Install congregate
RUN cd /opt/congregate && \
    chmod +x congregate && \
    cp congregate.sh /usr/local/bin/congregate && \
    pip install poetry


# RUN export PATH=$PATH:$HOME/.poetry/bin/poetry
RUN poetry install

# Initialize congregate directories
RUN congregate init

# Install Node
RUN npm install && \
    npm run build

RUN echo "alias ll='ls -ahl'" >> ~/.bashrc

# Only need 8000 currently. May need to expose more for upcoming mongo integration
EXPOSE 8000
