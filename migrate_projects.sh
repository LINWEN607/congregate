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

# Migrating user info
users=$(cat ${CONGREGATE_PATH}/data/users.json | jq .)
for ((i=0;i<`echo $users | jq '. | length'`;i++));
do
    user=$(echo $users | jq ".[$i]")
    curl --request POST --header "PRIVATE-TOKEN: $parentToken" \
        -H "Content-Type: application/json" -d "$user" $parentHost/api/v4/users
done

# Retrieving user info from parent instance for re-mapping
$new_users=$(curl --header "PRIVATE-TOKEN: $parentToken" -H "Content-Type: application/json" $parentHost/api/v4/users)
echo $new_users | jq . > ${CONGREGATE_PATH}/data/new_users.json

# Migrating group info
groups=$(cat ${CONGREGATE_PATH}/data/groups.json | jq .)
for ((i=0;i<`echo $groups | jq '. | length'`;i++));
do
    group=$(echo $groups | jq ".[$i]")
    echo $group
    curl --request POST --header "PRIVATE-TOKEN: $parentToken" \
        -H "Content-Type: application/json" -d "$group" $parentHost/api/v4/groups
done

# Retrieving group info from parent instance for re-mapping
$new_groups=$(curl --header "PRIVATE-TOKEN: $parentToken" -H "Content-Type: application/json" $parentHost/api/v4/groups)
echo $new_users | jq . > ${CONGREGATE_PATH}/data/new_groups.json

# Retrieving usable path information
path=$(echo $config | jq -r '.path')
workingDir=$(pwd)

# Iterating over staged projects
for ((i=0;i<`echo $files | jq '. | length'`;i++)); do
    name=$(echo $files | jq -r ".[$i].name")
    id=$(echo $files | jq -r ".[$i].id")
    namespace=$(echo $files | jq -r ".[$i].namespace")
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
    # Migrating projects from AWS S3 bucket
    elif [ "$location" == "aws" ] || [ "$location" == "AWS" ]; then
        echo "Exporting $name to S3"
        presigned_put_url=$(python ${CONGREGATE_PATH}/presigned.py $bucket_name $name.tar.gz PUT)
        curl --request POST --header "PRIVATE-TOKEN: $childToken" $childHost/api/v4/projects/$id/export \
            --data "upload[http_method]=PUT" \
            --data-urlencode "upload[url]=$presigned_put_url"
        
        # TODO: Add status check

        # Retrieving presigned url from AWS
        presigned_get_url=$(python ${CONGREGATE_PATH}/presigned.py $bucket_name $name.tar.gz GET)
        # Retrieving response from importing project
        imported_json=$(python import_from_s3.py $name $namespace $presigned_get_url)
        # Migrating project-specific variables to new instance
        python variable_migration.py "$imported_json" $id
    fi
done



cd $workingDir