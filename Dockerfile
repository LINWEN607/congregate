FROM python:2.7.15-stretch

# Define the ENV variable
ENV CONGREGATE_PATH /opt/congregate

WORKDIR /opt/congregate

# Copy supervisor configuration
ADD congregate congregate
COPY congregate.sh Pipfile ./
COPY js-packages/* ./js-packages/

# Installing some basic utilities and updating apt
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install less vim -y

# TODO: DB integration

# Install congregate
RUN cd /opt/congregate && \
    chmod +x congregate && \
    cp congregate.sh /usr/local/bin/congregate && \
    pip install pipenv && \
    pipenv install && \
    pipenv run dnd install

RUN echo "alias ll='ls -al'" >> ~/.bashrc

# Only need 8000 currently. May need to expose more for upcoming mongo integration
EXPOSE 8000
