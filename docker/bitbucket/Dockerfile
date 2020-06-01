FROM atlassian/bitbucket-server:latest

ARG BITBUCKET_LICENSE
ARG BITBUCKET_PASSWORD

ENV BITBUCKET_LICENSE=$BITBUCKET_LICENSE
ENV BITBUCKET_PASSWORD=$BITBUCKET_PASSWORD

EXPOSE 7990

COPY docker/bitbucket/bitbucket.properties-populated ./shared/bitbucket.properties
COPY docker/bitbucket/seed_data.sh /opt/seed_data.sh

ENTRYPOINT /opt/seed_data.sh


