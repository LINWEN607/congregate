FROM maven:3.8.6-openjdk-11

# Add ps-user and give them sudo privileges
RUN adduser ps-user && \
    usermod -aG sudo ps-user && \
    apt update && apt upgrade -y && apt install -y sudo apt-utils  && \
    sed -i 's/sudo.*ALL\=(ALL:ALL).*ALL/sudo ALL=(ALL) NOPASSWD:ALL/' /etc/sudoers

# Copy files
COPY docker/maven/settings.xml /opt/settings.xml
COPY docker/maven/maven_server.py /opt/maven_server.py
COPY congregate/migration/maven/maven_pb2_grpc.py /opt/maven_pb2_grpc.py
COPY congregate/migration/maven/maven_pb2.py /opt/maven_pb2.py

RUN apt-get install -y build-essential libncursesw5-dev \
    libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

RUN cd /opt && \
    curl https://www.python.org/ftp/python/3.8.12/Python-3.8.12.tgz -o Python-3.8.12.tgz && \
    tar xzf Python-3.8.12.tgz && \
    cd Python-3.8.12 && \
    ./configure --enable-optimizations && \
    make -j 2 && \
    sudo make altinstall && \
    cd /opt && \
    rm Python-3.8.12.tgz && \
    rm -r Python-3.8.12

# Install GRPC packages
RUN apt-get -y install python3-pip
RUN pip3 install grpcio grpcio-tools

WORKDIR /opt

EXPOSE 50051

USER ps-user

RUN mkdir /opt/project_repositories

ENTRYPOINT ["python3", "maven_server.py"]

