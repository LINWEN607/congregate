FROM python:2.7.15-stretch

ARG VERSION

# Define the ENV variable
ENV CONGREGATE_PATH /opt/congregate
 
# Copy supervisor configuration
COPY congregate-${VERSION}.tar.gz /opt

# TODO: DB integration

# Extract generated tar
RUN cd /opt && \
    tar -zxf congregate-${VERSION}.tar.gz  -C /opt && \
    mv congregate-${VERSION} congregate

# Install congregate
RUN cd /opt/congregate && \
    chmod +x congregate && \
    cp congregate /usr/local/bin && \
    pip install pipenv && \
    pipenv install

# Only need 8000 currently. May need to expose more for upcoming mongo integration
EXPOSE 8000