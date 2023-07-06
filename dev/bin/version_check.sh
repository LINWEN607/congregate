#!/bin/sh

STORED_VERSION=$(cat pyproject.toml | grep -e "^version" | awk '{print $3}' | tr -d '"')

if [ "$STORED_VERSION" != "$CI_COMMIT_TAG" ]; then 
    echo "Version mismatch. Please update pyproject.toml before cutting a tag"
    exit 1
fi