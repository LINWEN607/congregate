FROM python:2.7.15-stretch

# Define the ENV variable
ENV CONGREGATE_PATH /opt/congregate

WORKDIR /opt/congregate

# Copy supervisor configuration
ADD congregate congregate
COPY congregate.sh pyproject.toml README.md snakeskin.txt ./

# Installing some basic utilities and updating apt
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install less vim jq curl -y

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

RUN cd /opt/congregate && \
    poetry run dnd install

RUN echo "alias ll='ls -al'" >> ~/.bashrc

# Only need 8000 currently. May need to expose more for upcoming mongo integration
EXPOSE 8000
