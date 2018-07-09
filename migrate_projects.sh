#!/bin/bash

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

users=$(cat ${CONGREGATE_PATH}/data/users.json | jq .)
for ((i=0;i<`echo $users | jq '. | length'`;i++));
do
    user=$(echo $users | jq ".[$i]")
    curl --request POST --header "PRIVATE-TOKEN: $parentToken" \
        -H "Content-Type: application/json" -d "$user" $parentHost/api/v4/users
done

groups=$(cat groups.json | jq .)
for ((i=0;i<`echo $groups | jq '. | length'`;i++));
do
    group=$(echo $groups | jq ".[$i]")
    echo $group
    curl --request POST --header "PRIVATE-TOKEN: $parentToken" \
        -H "Content-Type: application/json" -d "$group" $parentHost/api/v4/groups
done


path=$(echo $config | jq -r '.path')
workingDir=$(pwd)

for ((i=0;i<`echo $files | jq '. | length'`;i++)); do
    name=$(echo $files | jq -r ".[$i].name")
    id=$(echo $files | jq -r ".[$i].id")
    namespace=$(echo $files | jq -r ".[$i].namespace")
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
    elif [ "$location" == "aws" ] || [ "$location" == "AWS" ]; then
        echo "Exporting $name to S3"
        presigned_put_url=$(python ${CONGREGATE_PATH}/presigned.py $bucket_name $name.tar.gz PUT)
        curl --request POST --header "PRIVATE-TOKEN: $childToken" $childHost/api/v4/projects/$id/export \
            --data "upload[http_method]=PUT" \
            --data-urlencode "upload[url]=$presigned_put_url"
        
        # Add status check here

        presigned_get_url=$(python ${CONGREGATE_PATH}/presigned.py $bucket_name $name.tar.gz GET)
        python import_from_s3.py $name $namespace $presigned_get_url
    fi
done

cd $workingDir