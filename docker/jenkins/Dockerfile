FROM jenkins/jenkins:lts

USER root

RUN apt update && \
    apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl libbz2-dev && \
    curl -O https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tar.xz && \
    tar -xf Python-3.8.2.tar.xz && \
    cd Python-3.8.2 && \
    ./configure --enable-optimizations && \
    make -j $(nproc) && \
    make altinstall

COPY setup_and_seed.py /opt/setup_and_seed.py

COPY entrypoint.sh /opt/entrypoint.sh

RUN python3.8 -m pip install requests python-jenkins

RUN chmod 777 /opt/setup_and_seed.py

USER jenkins

ENTRYPOINT ["/sbin/tini", "--", "/opt/entrypoint.sh"]
