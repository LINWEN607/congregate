FROM jenkins/jenkins:lts

USER root

RUN apt update && \
    apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl \
    libbz2-dev python3 python3-pip

COPY setup_and_seed.py /opt/setup_and_seed.py

COPY entrypoint.sh /opt/entrypoint.sh

RUN python3 -m pip install requests python-jenkins

RUN chmod 777 /opt/setup_and_seed.py

USER jenkins

ENTRYPOINT ["/sbin/tini", "--", "/opt/entrypoint.sh"]
