#!/bin/sh

TEST_IMAGE_NAME="$CI_REGISTRY_IMAGE/test:latest"

version=$(cat pyproject.toml | grep -e "^python = " | cut -d' ' -f3 | cut -c3- | rev | cut -c2- | rev)

if [ "$version" == "2.7" ]; then
    cp ./docker/test/py27.Dockerfile ./Dockerfile
    TEST_IMAGE_NAME="$CI_REGISTRY_IMAGE/test-2.7:latest"

elif [ "$version" == "3.8" ]; then
    cp ./docker/test/py38.Dockerfile ./Dockerfile
    TEST_IMAGE_NAME="$CI_REGISTRY_IMAGE/test-3.8:latest"
fi

docker build --tag "$TEST_IMAGE_NAME" .
docker push "$TEST_IMAGE_NAME"