#!/bin/bash

# Original source: https://medium.com/@pjbgf/moving-docker-images-from-one-container-registry-to-another-2f1f1631dc49
# This script is used to mass migrate docker containers within a single repository
# This is used for the tuple of tags version of the bulk import, so that it expects well-formatted inputs
# It also currently assumes that you've pre-staged the containers via a bulk pull

source_repo=$1
destination_repo=$2

# If you haven't pre-staged, uncomment this line
# docker pull $source_repo

# Re-tag to the new version and push
docker tag $source_repo $destination_repo
docker push $destination_repo