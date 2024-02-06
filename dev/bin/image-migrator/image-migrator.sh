#!/bin/bash

# Variables 

source config.sh

[[ -z "$SOURCE_USER" ]] && { echo "SOURCE_USER is empty, exiting ... " ; exit 1; }
[[ -z "$SOURCE_PAT" ]] && { echo "SOURCE_PAT is empty, exiting ... " ; exit 1; }
[[ -z "$TARGET_USER" ]] && { echo "TARGET_USER is empty, exiting ... " ; exit 1; }
[[ -z "$TARGET_PAT" ]] && { echo "TARGET_PAT is empty, exiting ... " ; exit 1; }
[[ -z "$BASE_URL_SOURCE" ]] && { echo "BASE_URL_SOURCE is empty, exiting ... " ; exit 1; }
[[ -z "$BASE_URL_TARGET" ]] && { echo "BASE_URL_TARGET is empty, exiting ... " ; exit 1; }

while read -r line; do

    IFS=' ' read -ra image <<< "$line"
    SOURCE_IMAGE=$image
    TARGET_IMAGE=$(echo $image | sed "s,$BASE_URL_SOURCE,$BASE_URL_TARGET,g")
    echo "Migrating $SOURCE_IMAGE => $TARGET_IMAGE"
    skopeo copy --src-creds=$SOURCE_USER:$SOURCE_PAT --dest-creds=$TARGET_USER:$TARGET_PAT docker://$SOURCE_IMAGE docker://$TARGET_IMAGE

done < images.yml