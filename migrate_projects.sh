#!/bin/bash

files=$(cat stage.json)

config=$(cat config.json | jq '.config')
childHost=$(echo $config | jq -r '.child_instance_host')
childToken=$(echo $config | jq -r '.child_instance_token')
parentHost=$(echo $config | jq -r '.parent_instance_host')
parentToken=$(echo $config | jq -r '.parent_instance_token')
location=$(echo $config | jq -r '.location')

users=$(cat users.json | jq .)
for ((i=0;i<`echo $users | jq '. | length'`;i++));
do
    user=$(echo $users | jq ".[$i]")
    curl --request POST --header "PRIVATE-TOKEN: $parentToken" -H "Content-Type: application/json" -d "$user" $parentHost/api/v4/users
done

groups=$(cat groups.json | jq .)
for ((i=0;i<`echo $groups | jq '. | length'`;i++));
do
    group=$(echo $groups | jq ".[$i]")
    echo $group
    curl --request POST --header "PRIVATE-TOKEN: $parentToken" -H "Content-Type: application/json" -d "$group" $parentHost/api/v4/groups
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
        curl --request POST --header "PRIVATE-TOKEN: $parentToken" --form "path=$name" --form "file=@$fullFilePath" --form "namespace=$namespace" $parentHost/api/v4/projects/import
    fi
done

cd $workingDir