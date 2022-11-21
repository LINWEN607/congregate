FROM jenkins/jenkins:lts

USER root

RUN apt update && \
    apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libsqlite3-dev libreadline-dev libffi-dev curl \
    libbz2-dev python3 python3-pip

COPY setup_and_seed.py /opt/setup_and_seed.py

COPY entrypoint.sh /opt/entrypoint.sh

RUN python3 -m pip install requests python-jenkins urllib3 charset_normalizer idna certifi multi_key_dict six

# Install plugins via CLI
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli -f /usr/share/jenkins/ref/plugins.txt

# It will probably reboot for the next layer
# Setup test job skipping plugins

RUN chmod 777 /opt/setup_and_seed.py

USER jenkins

ENTRYPOINT ["/usr/bin/tini", "--", "/opt/entrypoint.sh"]
