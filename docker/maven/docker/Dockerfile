FROM maven:3.8.6-openjdk-11

# Add ps-user and give them sudo privileges
RUN adduser ps-user && \
    usermod -aG sudo ps-user && \
    apt update && apt upgrade -y && apt install -y sudo apt-utils  && \
    sed -i 's/sudo.*ALL\=(ALL:ALL).*ALL/sudo ALL=(ALL) NOPASSWD:ALL/' /etc/sudoers

# Copy files
COPY command_server.py /opt/command_server.py
COPY cmd_pb2_grpc.py /opt/cmd_pb2_grpc.py
COPY cmd_pb2.py /opt/cmd_pb2.py
COPY pom.xml /opt/mymaven/pom.xml

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

ENTRYPOINT ["python3", "command_server.py"]

