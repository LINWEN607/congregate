#!/bin/bash

# Congregate - GitLab instance migration utility 
#
# Copyright (c) 2018 - GitLab
#
# Final migration script
#
# Steps:
# 1. Add uesrs from child instance
# 2. Add groups from child instance
# 3. Export projects to the configured storage location
# 4. Migrate projects from staged environment to parent instance
#

files=$(cat ${CONGREGATE_PATH}/data/stage.json)

config=$(cat ${CONGREGATE_PATH}/data/config.json | jq '.config')
childHost=$(echo $config | jq -r '.child_instance_host')
childToken=$(echo $config | jq -r '.child_instance_token')
parentHost=$(echo $config | jq -r '.parent_instance_host')
parentToken=$(echo $config | jq -r '.parent_instance_token')
location=$(echo $config | jq -r '.location')
bucket_name=$(echo $config | jq -r '.bucket_name')
access_key=$(echo $config | jq -r '.access_key')
secret_key=$(echo $config | jq -r '.secret_key')

# Migrating user info and update members in groups and projects
python ${CONGREGATE_PATH}/users.py --migrate=True --update=True

# Migrating group info
python ${CONGREGATE_PATH}/groups.py --migrate=True

# Retrieving usable path information
path=$(echo $config | jq -r '.path')
workingDir=$(pwd)

# Iterating over staged projects
for ((i=0;i<`echo $files | jq '. | length'`;i++)); do
    name=$(echo $files | jq -r ".[$i].name")
    id=$(echo $files | jq -r ".[$i].id")
    namespace=$(echo $files | jq -r ".[$i].namespace")
    project_json=$(echo $files | jq -r ".[$i]")
    # Migration projects from filesystem storage
    if [ $location == "filesystem" ]; then
        echo "Exporting $name to $path"
        curl -s --request POST --header "PRIVATE-TOKEN: $childToken" $childHost/api/v4/projects/$id/export
        if [ "$(pwd)" != "$path" ]; then
            cd $path
        fi
        download=$(curl --header "PRIVATE-TOKEN: $childToken" --remote-header-name --remote-name "$childHost/api/v4/projects/$id/export/download")
        downloadArray=($download)
        fileName=$(echo ${downloadArray[${#downloadArray[@]}-1]} | tr -d "'")
        fullFilePath=$(echo "$path/$fileName")
        curl --request POST --header "PRIVATE-TOKEN: $parentToken" \
            --form "path=$name" \
            --form "file=@$fullFilePath" \
            --form "namespace=$namespace" $parentHost/api/v4/projects/import
        
        python projects.py --migrate=True
    # Migrating projects from AWS S3 bucket
    elif [ "$location" == "aws" ] || [ "$location" == "AWS" ]; then
        echo "Exporting $name to S3"
        # TODO: Add status check

        python ${CONGREGATE_PATH}/projects.py --project_json "$project_json"

    fi
done



cd $workingDir