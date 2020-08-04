#!/bin/bash

# Original source: https://medium.com/@pjbgf/moving-docker-images-from-one-container-registry-to-another-2f1f1631dc49
# This script is used to mass migrate docker containers within a single repository
# Usage: 
# sudo -E ./manually_move_images.sh <source-repo> <target-repo>
# Example:
# sudo -E ./manually_move_images.sh registry.gitlab.com/gitlab-com/customer-success/tools/congregate registry.gitlab.com/move-this/to-here/actually-move-this/test-project

source_repo=$1
destination_repo=$2

# Download all images
docker pull $source_repo --all-tags

# Get all images published after $minimum_version
# format output to be: 
#   docker tag source_repo_NAME:VERSION TARGET_IMAGE_NAME:VERSION |
#   docker push TARGET_IMAGE_NAME:VERSION
# finally, execute those as commands
docker images $source_repo \
  --format "docker tag {{.Repository}}:{{.Tag}} $destination_repo:{{.Tag}} | docker push $destination_repo:{{.Tag}}" | 
  bash